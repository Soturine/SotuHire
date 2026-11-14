"""CP-DATA01: the user states a fact once in the Universal Profile and the resume reuses it.

Authority under test: Profile (source of truth) -> Master Resume (derived, editable) -> variant
(derived, job-specific). Only confirmed, non-sensitive facts flow downstream, every projected entry
keeps the profile item id, later profile facts arrive only through a reviewed apply, and nothing
written to the resume or a variant changes the profile.
"""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path

from docx import Document
from modules.profile.models import ProfileItem
from modules.profile.service import UniversalCareerProfileService
from tests.api_test_helpers import api_client

STUDIO = "/api/v1/resume-studio"


def _seed_profile() -> dict[str, str]:
    service = UniversalCareerProfileService()
    service.update_profile(
        {
            "summary": "Enfermeira com foco em segurança do paciente.",
            "target_roles": ["Enfermeira UTI"],
        }
    )
    ids = {}
    for key, item, confirmed in (
        (
            "work",
            ProfileItem(
                type="experience",
                title="Enfermeira assistencial",
                organization="Hospital Fictício",
                start_date="2021-03",
                description="Plantões em UTI adulto.",
            ),
            True,
        ),
        (
            "education",
            ProfileItem(
                type="education",
                title="Bacharelado em Enfermagem",
                institution="Universidade Fictícia",
            ),
            True,
        ),
        (
            "registry",
            ProfileItem(type="certification", title="COREN ativo", organization="COREN-SP"),
            True,
        ),
        ("candidate", ProfileItem(type="experience", title="Estágio não revisado"), False),
        (
            "sensitive",
            ProfileItem(type="experience", title="Afastamento médico", sensitive=True),
            True,
        ),
    ):
        ids[key] = service.add_item(item, confirmed_by_user=confirmed).item_id
    return ids


def _titles(resume: dict) -> dict[str, list[str]]:
    return {s["section_type"]: [e["title"] for e in s["entries"]] for s in resume["sections"]}


def test_master_resume_is_built_from_confirmed_profile_facts_without_retyping(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    ids = _seed_profile()
    client = api_client()

    created = client.post(f"{STUDIO}/master/from-profile", json={})
    assert created.status_code == 201, created.text
    resume = created.json()["data"]["resume"]

    assert resume["source_type"] == "profile"
    assert resume["summary"] == "Enfermeira com foco em segurança do paciente."
    assert resume["target_role"] == "Enfermeira UTI"
    assert _titles(resume) == {
        "experience": ["Enfermeira assistencial"],
        "education": ["Bacharelado em Enfermagem"],
        "certifications": ["COREN ativo"],
    }
    entry = resume["sections"][0]["entries"][0]
    assert entry["source_profile_item_ids"] == [ids["work"]]
    assert entry["subtitle"] == "Hospital Fictício" and entry["confirmed_by_user"] is True
    assert "Estágio não revisado" not in json.dumps(resume)
    assert "Afastamento médico" not in json.dumps(resume)
    assert any("não confirmado" in w for w in resume["validation_warnings"])
    # the same GET the Resume Studio uses now returns it
    assert (
        client.get(f"{STUDIO}/master").json()["data"]["resume"]["master_resume_id"]
        == resume["master_resume_id"]
    )
    # a second creation would overwrite the user's edits: refused
    assert client.post(f"{STUDIO}/master/from-profile", json={}).status_code == 409


def test_later_profile_facts_reach_the_resume_only_after_review_and_never_flow_back(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    ids = _seed_profile()
    client = api_client()
    client.post(f"{STUDIO}/master/from-profile", json={})
    assert client.get(f"{STUDIO}/master/profile-updates").json()["data"]["items"] == []

    added = UniversalCareerProfileService().add_item(
        ProfileItem(type="language", title="Inglês intermediário")
    )
    pending = client.get(f"{STUDIO}/master/profile-updates").json()["data"]["items"]
    assert [(i["item_id"], i["section_title"]) for i in pending] == [(added.item_id, "Idiomas")]
    master_before = client.get(f"{STUDIO}/master").json()["data"]["resume"]
    assert "Inglês intermediário" not in json.dumps(master_before)  # nothing changes on its own

    for forbidden in (ids["candidate"], ids["sensitive"], "missing-id"):
        rejected = client.post(f"{STUDIO}/master/profile-updates", json={"item_ids": [forbidden]})
        assert rejected.status_code == 422

    applied = client.post(f"{STUDIO}/master/profile-updates", json={"item_ids": [added.item_id]})
    assert applied.status_code == 200
    assert _titles(applied.json()["data"]["resume"])["languages"] == ["Inglês intermediário"]
    assert client.get(f"{STUDIO}/master/profile-updates").json()["data"]["items"] == []

    # A job variant edits its own copy; the profile and the master keep the original fact.
    master = applied.json()["data"]["resume"]
    variant = {
        "resume_variant_id": "variant-uti",
        "master_resume_id": master["master_resume_id"],
        "title": "Variante UTI",
        "target_role": "Enfermeira UTI",
        "sections": master["sections"],
        "source_profile_item_ids": master["source_profile_item_ids"],
    }
    variant["sections"][0]["entries"][0]["content"] = "Texto ajustado só para esta vaga."
    saved = client.post(f"{STUDIO}/variants", json={"variant": variant})
    assert saved.status_code == 200, saved.text
    profile_after = UniversalCareerProfileService().get_profile()
    work = next(i for i in profile_after.items if i.item_id == ids["work"])
    assert work.description == "Plantões em UTI adulto."
    assert "Texto ajustado" not in json.dumps(client.get(f"{STUDIO}/master").json())

    # The export is built from the reviewed variant, accents included.
    exported = client.post(f"{STUDIO}/variants/variant-uti/export", json={"format": "docx"})
    assert exported.status_code == 200, exported.text
    payload = exported.json()["data"]["payload"] or {}
    content = payload.get("content_base64") or exported.json()["data"]["export"].get(
        "content_base64", ""
    )
    text = "\n".join(p.text for p in Document(io.BytesIO(base64.b64decode(content))).paragraphs)
    assert "Texto ajustado só para esta vaga." in text and "Bacharelado em Enfermagem" in text


def test_an_empty_profile_gets_a_clear_message_instead_of_an_empty_resume(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    response = api_client().post(f"{STUDIO}/master/from-profile", json={})
    assert response.status_code == 422
    assert "confirmados" in response.json()["error"]["message"] or "confirmados" in response.text
