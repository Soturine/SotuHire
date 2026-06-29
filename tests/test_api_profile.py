from __future__ import annotations

import json
from pathlib import Path

from tests.api_test_helpers import api_client


def test_profile_crud_import_context_and_dedupe(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    default_profile = client.get("/api/v1/profile")
    assert default_profile.status_code == 200
    assert default_profile.json()["data"]["profile"]["profile_id"] == "default"

    updated = client.put(
        "/api/v1/profile",
        json={
            "display_name": "Pessoa Ficticia",
            "headline": "Estudante de engenharia em busca de estagio",
            "primary_domains": ["Engenharia"],
            "target_roles": ["Estagio em Engenharia"],
            "preferred_locations": ["Sao Jose dos Campos"],
            "preferred_work_models": ["hibrido"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["profile"]["display_name"] == "Pessoa Ficticia"

    created = client.post(
        "/api/v1/profile/items",
        json={
            "type": "certification",
            "title": "NR10",
            "domain": "Engenharia",
            "evidence": "Certificado NR10 informado pelo usuario.",
            "source": "manual",
        },
    )
    assert created.status_code == 200
    item = created.json()["data"]["item"]
    assert item["confirmed_by_user"] is True
    assert item["confidence"] == "high"

    patched = client.patch(
        f"/api/v1/profile/items/{item['item_id']}",
        json={"description": "Certificado NR10 revisado pelo usuario."},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["item"]["confirmed_by_user"] is True

    imported = client.post(
        "/api/v1/profile/import-text",
        json={
            "text": "Tenho CREA e experiencia em obra. Tambem fiz curso de AutoCAD.",
            "source_type": "manual_notes",
            "use_ai": False,
        },
    )
    assert imported.status_code == 200
    draft = imported.json()["data"]
    assert draft["needs_user_review"] is True
    assert draft["analysis_mode"] == "local"
    assert any(draft_item["title"] == "CREA" for draft_item in draft["items"])
    assert all(draft_item["confirmed_by_user"] is False for draft_item in draft["items"])

    duplicate = client.post(
        "/api/v1/profile/items",
        json={
            "type": "certification",
            "title": "NR10",
            "domain": "Engenharia",
            "evidence": "Mesmo certificado em outra fonte ficticia.",
            "source": "certificate",
        },
    )
    assert duplicate.status_code == 200

    dedupe = client.post("/api/v1/profile/deduplicate")
    assert dedupe.status_code == 200
    assert dedupe.json()["data"]["suggestions"]

    context = client.get("/api/v1/profile/context")
    assert context.status_code == 200
    payload = context.json()
    serialized = json.dumps(payload).lower()
    assert payload["data"]["context"]["career_goals"] == ["Estagio em Engenharia"]
    assert any(
        signal["title"] == "NR10"
        for signal in payload["data"]["context"]["certifications_and_registries"]
    )
    assert "api_key" not in serialized
    assert "secret" not in serialized

    deleted = client.delete(f"/api/v1/profile/items/{item['item_id']}")
    assert deleted.status_code == 200
    remaining_ids = {
        remaining["item_id"] for remaining in deleted.json()["data"]["profile"]["items"]
    }
    assert item["item_id"] not in remaining_ids


def test_profile_import_local_supports_multi_area_examples(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    examples = [
        ("Estudante de engenharia buscando estagio com obra e CREA.", "CREA", "Engenharia"),
        ("Enfermeiro com COREN e experiencia hospitalar.", "COREN", "Saude"),
        ("Advogado com OAB e atuacao em audiencias.", "OAB", "Direito"),
        ("Professor com licenciatura e sala de aula.", "Pratica docente", "Educacao"),
        ("Designer com portfolio no Behance.", "Portfolio", "Artes e Design"),
        (
            "Pesquisador com Lattes e iniciacao cientifica em laboratorio.",
            "Pesquisa",
            "Pesquisa e Laboratorio",
        ),
        ("Tecnico industrial com NR10 e NR35.", "NR10", "Engenharia"),
        ("Psicologo com CRP e atendimento clinico.", "CRP", "Saude"),
        ("Quimica com CRQ e pratica de laboratorio.", "CRQ", "Pesquisa e Laboratorio"),
        ("Guia de turismo com ingles e espanhol.", "Inglês, Espanhol", "Turismo e Servicos"),
    ]

    for text, expected_title, expected_domain in examples:
        response = client.post(
            "/api/v1/profile/import-text",
            json={"text": text, "source_type": "manual_notes", "use_ai": False},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        titles = {item["title"] for item in data["items"]}
        assert expected_title in titles
        assert expected_domain in data["detected_domains"]
        assert data["needs_user_review"] is True
        assert all(item["confirmed_by_user"] is False for item in data["items"])


def test_wishlist_draft_uses_persisted_profile_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    client.put(
        "/api/v1/profile",
        json={
            "display_name": "Pessoa Ficticia",
            "target_roles": ["Guia de Turismo"],
            "preferred_locations": ["Recife"],
            "preferred_work_models": ["presencial"],
        },
    )
    client.post(
        "/api/v1/profile/items",
        json={
            "type": "technical_skill",
            "title": "Ingles",
            "domain": "Turismo e Servicos",
            "source": "manual",
            "evidence": "Curso de idioma informado pelo usuario.",
        },
    )

    response = client.post(
        "/api/v1/radar/wishlists/draft",
        json={"free_text": "Busco oportunidades com atendimento.", "use_profile_context": True},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["needs_user_review"] is True
    assert "Guia de Turismo" in data["wishlist"]["target_titles"]
    assert "Ingles" in data["wishlist"]["required_skills"]
    assert "Recife" in data["wishlist"]["locations"]


def test_profile_import_with_mocked_ai_requires_review_and_hides_secret(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class FakeProvider:
        name = "gemini"

        def generate_structured(self, prompt, payload):  # noqa: ANN001
            assert prompt.prompt_id == "profile_items_extractor_v1"
            serialized_payload = json.dumps(payload).lower()
            assert "api_key" not in serialized_payload
            assert "fake-profile-secret" not in serialized_payload
            return {
                "items": [
                    {
                        "type": "professional_registry",
                        "title": "COREN",
                        "description": "Texto informa COREN.",
                        "domain": "Saude",
                        "area": "Saude",
                        "evidence": "Tenho COREN e experiencia hospitalar.",
                        "source": "resume",
                        "confidence": "high",
                        "confirmed_by_user": True,
                    }
                ],
                "detected_domains": ["Saude"],
                "career_moments": ["junior"],
                "warnings": [],
                "questions_to_confirm": ["Qual numero do registro, se o usuario quiser informar?"],
                "provider_used": "gemini",
                "requested_provider": "gemini",
                "analysis_mode": "ai",
                "needs_user_review": False,
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
        "/api/v1/profile/import-text",
        json={
            "text": "Tenho COREN e experiencia hospitalar.",
            "source_type": "resume",
            "use_ai": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    assert data["analysis_mode"] == "ai"
    assert data["provider_used"] == "gemini"
    assert data["needs_user_review"] is True
    assert data["items"][0]["confirmed_by_user"] is False
    serialized = json.dumps(payload).lower()
    assert "api_key" not in serialized
    assert "fake-profile-secret" not in serialized


def test_profile_import_ai_failure_falls_back_to_local(tmp_path: Path, monkeypatch) -> None:
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
        "/api/v1/profile/import-text",
        json={"text": "Sou advogada com OAB.", "source_type": "resume", "use_ai": True},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_mode"] == "fallback"
    assert data["provider_used"] == "local"
    assert any(item["title"] == "OAB" for item in data["items"])


def test_profile_import_rejects_empty_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post(
        "/api/v1/profile/import-text",
        json={"text": "   ", "source_type": "resume"},
    )

    assert response.status_code == 422
