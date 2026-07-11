from __future__ import annotations

import json
from pathlib import Path

from modules.academic import LattesImportInput, LattesService, parse_lattes_text
from modules.profile.service import UniversalCareerProfileService
from modules.profile.store import UniversalCareerProfileStore
from tests.api_test_helpers import api_client

LATTES_TEXT = """
Identificação
Endereço para acessar este CV: http://lattes.cnpq.br/1234567890123456
ORCID: 0000-0002-1825-0097

Formação acadêmica/titulação
2022 - 2024 Mestrado em Geofísica Espacial. Universidade do Vale do Paraíba.

Projetos de pesquisa
2021 - 2022 Projeto de pesquisa em ionosfera com análise de dados em Python. PIBIC/CNPq.

Projetos de extensão
2020 Projeto de extensão em divulgação científica para escolas públicas.

Artigos completos publicados em periódicos
SILVA, A.; SOUZA, B. Estudo da ionosfera. Revista Fictícia, 2024. DOI: 10.1234/abc.def

Monitoria
2019 Monitoria em Física I.

Docência
2023 Docência na disciplina Introdução à Física Experimental.
"""


def test_lattes_parser_detects_academic_sections_and_items() -> None:
    result = parse_lattes_text(
        LattesImportInput(
            text=LATTES_TEXT,
            source_url="http://lattes.cnpq.br/1234567890123456",
        )
    )

    types = {item.type for item in result.items}

    assert "Formação acadêmica/titulação" in result.detected_sections
    assert "lattes_identifier" in types
    assert "orcid" in types
    assert "master_degree" in types
    assert "research_project" in types
    assert "extension_project" in types
    assert "journal_article" in types
    assert "monitoring" in types
    assert "teaching_experience" in types
    assert any(item.source_ref == "10.1234/abc.def" for item in result.items)
    assert result.needs_user_review is True
    assert all(item.confirmed_by_user is False for item in result.items)


def test_lattes_parser_does_not_invent_identifiers() -> None:
    result = parse_lattes_text(
        LattesImportInput(
            text="Projetos de pesquisa\nProjeto sem DOI, ORCID, URL ou identificador informado."
        )
    )

    identifiers = [item.source_ref or "" for item in result.items]

    assert not any(identifier.startswith("10.") for identifier in identifiers)
    assert not any(item.type == "orcid" for item in result.items)
    assert not any(item.type == "lattes_identifier" for item in result.items)


def test_lattes_import_local_does_not_save_until_confirm(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    draft_response = client.post(
        "/api/v1/profile/import-lattes",
        json={"text": LATTES_TEXT, "use_ai": False},
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()["data"]
    assert draft["analysis_mode"] == "local"
    assert draft["needs_user_review"] is True
    assert draft["items"]
    assert all(item["confirmed_by_user"] is False for item in draft["items"])

    empty_profile = client.get("/api/v1/profile").json()["data"]["profile"]
    assert empty_profile["items"] == []

    confirm_response = client.post(
        "/api/v1/profile/lattes/confirm",
        json={"items": draft["items"][:2]},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["data"]
    assert confirmed["saved"]
    assert all(item["confirmed_by_user"] is True for item in confirmed["saved"])
    assert {item["source"] for item in confirmed["saved"]} == {"curriculum_lattes"}

    saved_profile = client.get("/api/v1/profile").json()["data"]["profile"]
    assert len(saved_profile["items"]) == len(confirmed["saved"])

    duplicate_response = client.post(
        "/api/v1/profile/lattes/confirm",
        json={"items": draft["items"][:2]},
    )
    assert duplicate_response.status_code == 200
    duplicate_data = duplicate_response.json()["data"]
    assert not duplicate_data["saved"]
    assert duplicate_data["skipped_duplicates"]


def test_lattes_import_with_mocked_gemini_still_requires_review(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class FakeProvider:
        name = "gemini"

        def generate_structured(self, prompt, payload):  # noqa: ANN001
            assert prompt.prompt_id == "profile_lattes_extractor_v1"
            serialized_payload = json.dumps(payload).lower()
            assert "api_key" not in serialized_payload
            return {
                "items": [
                    {
                        "type": "journal_article",
                        "title": "Artigo em periódico fictício",
                        "description": "Texto explícito do artigo.",
                        "domain": "Produção científica",
                        "evidence": "Artigo publicado em periódico fictício.",
                        "source": "curriculum_lattes",
                        "source_ref": "10.1234/teste",
                        "confidence": "high",
                        "confirmed_by_user": True,
                        "sensitive": False,
                    }
                ],
                "detected_sections": ["Artigos completos publicados em periódicos"],
                "assumptions": [],
                "questions_to_confirm": [],
                "warnings": [],
                "confidence": "high",
                "needs_user_review": False,
                "provider_used": "gemini",
                "requested_provider": "gemini",
                "analysis_mode": "ai",
            }

    monkeypatch.setattr(
        "apps.api.services.profile.get_ai_runtime",
        lambda feature: type(
            "Runtime",
            (),
            {
                "provider": FakeProvider(),
                "provider_name": "gemini",
                "requested_provider": "gemini",
                "use_ai": True,
                "warnings": [],
            },
        )(),
    )
    client = api_client()

    response = client.post(
        "/api/v1/profile/lattes/draft",
        json={"text": LATTES_TEXT, "use_ai": True},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_mode"] == "ai"
    assert data["provider_used"] == "gemini"
    assert data["needs_user_review"] is True
    assert data["items"][0]["confirmed_by_user"] is False
    assert data["items"][0]["source"] == "curriculum_lattes"


def test_lattes_import_ai_failure_falls_back_to_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class BadProvider:
        name = "gemini"

        def generate_structured(self, prompt, payload):  # noqa: ANN001, ARG002
            return {"items": [{"title": "", "confidence": "impossivel"}]}

    monkeypatch.setattr(
        "apps.api.services.profile.get_ai_runtime",
        lambda feature: type(
            "Runtime",
            (),
            {
                "provider": BadProvider(),
                "provider_name": "gemini",
                "requested_provider": "gemini",
                "use_ai": True,
                "warnings": [],
            },
        )(),
    )
    client = api_client()

    response = client.post(
        "/api/v1/profile/import-lattes",
        json={"text": LATTES_TEXT, "use_ai": True},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_mode"] == "fallback"
    assert data["provider_used"] == "local"
    assert any(item["type"] == "research_project" for item in data["items"])


def test_lattes_service_confirm_marks_selected_items_only(tmp_path: Path) -> None:
    service = LattesService()
    draft = service.draft_local(LattesImportInput(text=LATTES_TEXT))
    selected = [item for item in draft.items if item.type in {"journal_article"}]

    profile_service = UniversalCareerProfileService(
        UniversalCareerProfileStore(tmp_path / "profiles.json")
    )
    result = service.confirm_items(selected, profile_service=profile_service)

    assert len(result.saved) == 1
    assert result.saved[0].confirmed_by_user is True
    assert result.saved[0].source == "curriculum_lattes"
    assert profile_service.get_profile().items[0].type == "journal_article"


def test_lattes_confirm_rejects_empty_selection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post("/api/v1/profile/lattes/confirm", json={"items": []})

    assert response.status_code == 422
