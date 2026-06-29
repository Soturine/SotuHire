from __future__ import annotations

import json
from pathlib import Path

from tests.api_test_helpers import api_client

FAKE_KEY = "AIza-fake-wishlist-key"


def test_wishlist_draft_local_from_free_text_is_not_saved(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post(
        "/api/v1/radar/wishlists/draft",
        json={
            "free_text": (
                "Sou estudante de engenharia, procuro estagio hibrido em Sao Jose dos Campos, "
                "com Excel, relatorios tecnicos e qualidade. Nao quero PJ."
            ),
            "use_profile_context": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    assert data["needs_user_review"] is True
    assert data["analysis_mode"] == "local"
    assert "Engenharia" in data["detected_domains"]
    assert "Estagio em Engenharia" in data["wishlist"]["target_titles"]
    assert "PJ" in data["wishlist"]["excluded_terms"]
    assert "api_key" not in json.dumps(payload).lower()

    saved = client.get("/api/v1/radar/wishlists")
    assert saved.status_code == 200
    assert saved.json()["data"]["wishlists"] == []


def test_wishlist_draft_rejects_empty_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post("/api/v1/radar/wishlists/draft", json={"free_text": "   "})

    assert response.status_code == 422


def test_wishlist_draft_rejects_oversized_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post(
        "/api/v1/radar/wishlists/draft",
        json={"free_text": "vaga " * 1_100},
    )

    assert response.status_code == 422


def test_wishlist_draft_supports_multi_area_non_tech_examples(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    examples = [
        ("Tenho COREN e busco enfermagem hospitalar em UTI.", "Saude", "COREN"),
        ("Sou formado em direito, com OAB, busco advocacia junior.", "Direito", "OAB"),
        ("Sou professor com licenciatura e quero trabalhar em escola.", "Educacao", ""),
        (
            "Sou tecnico industrial com NR10 e NR35 e busco manutencao.",
            "Engenharia",
            "NR10",
        ),
        (
            "Tenho portfolio de ilustracao e quero design ou producao cultural.",
            "Artes e Design",
            "",
        ),
        ("Tenho Lattes e iniciacao cientifica em laboratorio.", "Pesquisa e Laboratorio", "Lattes"),
        ("Sou guia de turismo com ingles e espanhol.", "Turismo e Servicos", ""),
        ("Sou psicologa com CRP e busco atendimento clinico.", "Saude", "CRP"),
        ("Sou medico com CRM e busco hospital ou pronto atendimento.", "Saude", "CRM"),
        ("Engenharia civil com CREA e experiencia em obra.", "Engenharia", "CREA"),
        ("Quimica com CRQ e experiencia em laboratorio.", "Pesquisa e Laboratorio", "CRQ"),
    ]

    for free_text, expected_domain, explicit_requirement in examples:
        response = client.post(
            "/api/v1/radar/wishlists/draft",
            json={"free_text": free_text, "use_profile_context": False},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert expected_domain in data["detected_domains"]
        assert data["needs_user_review"] is True
        assert data["wishlist"]["target_titles"]
        if explicit_requirement:
            assert explicit_requirement in data["wishlist"]["required_skills"]
        serialized = json.dumps(data).lower()
        assert "github" not in serialized
        assert "react" not in serialized


def test_wishlist_draft_does_not_assume_professional_registry(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post(
        "/api/v1/radar/wishlists/draft",
        json={
            "free_text": "Busco vaga hospitalar com triagem e atendimento.",
            "use_profile_context": False,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "Saude" in data["detected_domains"]
    assert "COREN" not in data["wishlist"]["required_skills"]
    assert "CRM" not in data["wishlist"]["required_skills"]


def test_wishlist_draft_uses_fake_gemini_valid_json_without_returning_secret(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class FakeGeminiProvider:
        name = "gemini"

        def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
            self.api_key = api_key or ""
            self.model = model or "gemini-wishlist-test"

        def generate_structured(self, prompt, payload):  # noqa: ANN001
            assert prompt.prompt_id == "job_wishlist_builder_v1"
            serialized_payload = json.dumps(payload).lower()
            assert "api_key" not in serialized_payload
            assert FAKE_KEY.lower() not in serialized_payload
            return {
                "wishlist": {
                    "name": "Wishlist IA revisavel",
                    "target_titles": ["Assistente de Pesquisa"],
                    "target_domains": ["Pesquisa e Laboratorio"],
                    "target_seniority": ["junior"],
                    "required_skills": ["metodologia", "relatorio"],
                    "desired_skills": ["Lattes"],
                    "excluded_terms": [],
                    "locations": ["Brasil"],
                    "remote_preferences": [],
                    "work_model": "",
                    "employment_type": "",
                    "salary_currency": "BRL",
                    "contract_types": ["bolsa"],
                    "industries": ["Pesquisa e Laboratorio"],
                    "companies_include": [],
                    "companies_exclude": [],
                    "source_types": ["public_feed"],
                    "min_match_score": 72,
                    "min_ats_score": 60,
                    "notify_on_new_matches": True,
                    "is_active": True,
                    "notes": "Revisar antes de salvar.",
                },
                "confidence": 0.81,
                "detected_domains": ["Pesquisa e Laboratorio"],
                "detected_career_moments": ["junior"],
                "assumptions": ["Texto cita pesquisa."],
                "questions_to_confirm": ["Qual area de laboratorio?"],
                "warnings": [],
                "needs_user_review": True,
                "provider_used": "gemini",
                "analysis_mode": "ai",
            }

    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", FakeGeminiProvider)
    client = api_client()
    ai_settings = client.post(
        "/api/v1/settings/ai",
        json={
            "provider": "gemini",
            "model": "gemini-wishlist-test",
            "api_key": FAKE_KEY,
            "use_ai": True,
            "allow_radar": True,
        },
    )
    assert ai_settings.status_code == 200

    response = client.post(
        "/api/v1/radar/wishlists/draft",
        json={"free_text": "Busco bolsa junior em pesquisa de laboratorio com Lattes."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["analysis_mode"] == "ai"
    assert payload["data"]["provider_used"] == "gemini"
    assert payload["data"]["needs_user_review"] is True
    serialized = json.dumps(payload).lower()
    assert FAKE_KEY.lower() not in serialized
    assert "api_key" not in serialized


def test_wishlist_draft_invalid_ai_json_falls_back_to_local(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class BadGeminiProvider:
        name = "gemini"

        def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
            self.model = model or "gemini-bad-json"

        def generate_structured(self, prompt, payload):  # noqa: ANN001, ARG002
            return {"wishlist": {"target_titles": "nao e lista"}, "confidence": 2}

    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", BadGeminiProvider)
    client = api_client()
    client.post(
        "/api/v1/settings/ai",
        json={
            "provider": "gemini",
            "model": "gemini-bad-json",
            "api_key": FAKE_KEY,
            "use_ai": True,
            "allow_radar": True,
        },
    )

    response = client.post(
        "/api/v1/radar/wishlists/draft",
        json={"free_text": "Quero vaga junior em direito com OAB."},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_mode"] == "fallback"
    assert data["provider_used"] == "local"
    assert "Direito" in data["detected_domains"]


def test_wishlist_draft_radar_toggle_off_uses_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    client.post(
        "/api/v1/settings/ai",
        json={
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "api_key": FAKE_KEY,
            "use_ai": True,
            "allow_radar": False,
        },
    )

    response = client.post(
        "/api/v1/radar/wishlists/draft",
        json={"free_text": "Procuro turismo com idiomas e atendimento."},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_mode"] in {"local", "fallback"}
    assert data["provider_used"] == "local"
    assert any("radar" in warning.lower() for warning in data["warnings"])
