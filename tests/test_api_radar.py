from __future__ import annotations

import json
from pathlib import Path

from modules.scraping.schemas import FetchResult
from tests.api_test_helpers import RESUME_TEXT, api_client

FAKE_KEY = "AIza-fake-radar-key"


RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Feed ficticio</title>
    <item>
      <title>Desenvolvedor Backend Python</title>
      <link>https://example.com/jobs/radar-1</link>
      <description>Cargo: Desenvolvedor Backend Python. Empresa: Empresa Exemplo. Localizacao: Remoto. Requisitos: Python, FastAPI e SQL.</description>
    </item>
  </channel>
</rss>
"""


def _fake_fetch(self, url: str, *, delay_seconds: float = 0.2) -> FetchResult:
    return FetchResult(
        url=url,
        status_code=200,
        content_type="application/rss+xml",
        text=RSS_XML,
    )


def _create_wishlist(client) -> str:
    response = client.post(
        "/api/v1/radar/wishlists",
        json={
            "name": "Backend Python remoto",
            "target_titles": ["Desenvolvedor Backend"],
            "required_skills": ["Python", "FastAPI", "SQL"],
            "desired_skills": ["Pytest"],
            "locations": ["Remoto"],
            "remote_preferences": ["remoto"],
            "min_match_score": 70,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["wishlist"]["id"]


def _create_rss_source(client) -> str:
    response = client.post(
        "/api/v1/radar/sources",
        json={
            "name": "Feed publico ficticio",
            "source_type": "public_feed",
            "url": "https://example.com/jobs.xml",
            "max_results": 10,
            "rate_limit_seconds": 0.2,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["source"]["id"]


def test_radar_wishlist_source_run_alert_and_save_actions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("modules.scraping.client.ScrapingClient.fetch", _fake_fetch)
    client = api_client()
    wishlist_id = _create_wishlist(client)
    source_id = _create_rss_source(client)

    patched = client.patch(
        f"/api/v1/radar/wishlists/{wishlist_id}",
        json={"desired_skills": ["Pytest", "Docker"], "min_ats_score": 40},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["wishlist"]["min_ats_score"] == 40

    run = client.post(
        "/api/v1/radar/run",
        json={"source_ids": [source_id], "wishlist_id": wishlist_id, "resume_text": RESUME_TEXT},
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["data"]["run"]["total_found"] == 1
    assert payload["data"]["run"]["total_alerted"] == 1
    result = payload["data"]["results"][0]
    assert result["source_type"] == "public_feed"
    assert result["radar_score"] >= 70
    assert result["radar_status"] == "matched"
    assert payload["data"]["alerts"]
    assert "api_key" not in json.dumps(payload).lower()

    alert_id = payload["data"]["alerts"][0]["id"]
    read = client.patch(f"/api/v1/radar/alerts/{alert_id}", json={"status": "read"})
    assert read.status_code == 200
    assert read.json()["data"]["alert"]["status"] == "read"

    result_id = result["id"]
    inbox = client.post(f"/api/v1/radar/results/{result_id}/save-inbox")
    assert inbox.status_code == 200
    assert inbox.json()["data"]["inbox_item"]["origin"] == "public_feed"
    assert inbox.json()["data"]["inbox_item"]["metadata"]["source_flow"] == "job_radar"

    tracker = client.post(f"/api/v1/radar/results/{result_id}/save-tracker")
    assert tracker.status_code == 200
    assert tracker.json()["data"]["tracker_id"]

    stats = client.get("/api/v1/radar/stats")
    assert stats.status_code == 200
    assert stats.json()["data"]["unread_alerts"] == 0


def test_radar_dedupes_repeated_results_and_guides_planned_sources(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("modules.scraping.client.ScrapingClient.fetch", _fake_fetch)
    client = api_client()
    wishlist_id = _create_wishlist(client)
    source_id = _create_rss_source(client)
    api_source = client.post(
        "/api/v1/radar/sources",
        json={
            "name": "API oficial planejada",
            "source_type": "official_api",
            "url": "https://api.example.com/jobs",
            "docs_url": "https://example.com/docs",
            "status": "available",
        },
    )
    assert api_source.status_code == 200
    assert api_source.json()["data"]["source"]["status"] == "requires_official_api"

    first = client.post(
        "/api/v1/radar/run",
        json={"source_ids": [source_id], "wishlist_id": wishlist_id},
    )
    second = client.post(
        "/api/v1/radar/run",
        json={"source_ids": [source_id, api_source.json()["data"]["source"]["id"]]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["data"]["run"]["total_deduped"] >= 1
    assert second_payload["data"]["run"]["total_errors"] >= 1
    assert second_payload["data"]["results"][0]["radar_status"] == "duplicate"


def test_radar_ai_explanation_uses_provider_without_returning_secret(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("modules.scraping.client.ScrapingClient.fetch", _fake_fetch)

    class FakeGeminiProvider:
        name = "gemini"

        def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
            self.api_key = api_key or ""
            self.model = model or "gemini-radar-test"

        def generate_structured(self, prompt, payload):  # noqa: ANN001
            assert prompt.prompt_id == "job_radar_match_explanation_v1"
            assert "api_key" not in json.dumps(payload).lower()
            return {
                "summary": "Vaga ficticia alinha Python e FastAPI.",
                "match_reasons": ["Python e FastAPI aparecem na fonte."],
                "evidence": ["Descricao cita Python, FastAPI e SQL."],
                "gaps": ["Validar requisitos completos antes de salvar."],
                "recommended_actions": ["Salvar na Caixa de Entrada para revisar."],
                "tags": ["Python", "FastAPI"],
                "domain": "tecnologia",
                "seniority": "pleno",
                "warnings": [],
                "confidence": 0.78,
            }

    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", FakeGeminiProvider)
    client = api_client()
    ai_settings = client.post(
        "/api/v1/settings/ai",
        json={
            "provider": "gemini",
            "model": "gemini-radar-test",
            "api_key": FAKE_KEY,
            "use_ai": True,
            "allow_match": True,
            "allow_ats": True,
            "allow_tailor": True,
            "allow_github": True,
            "allow_memory_context": False,
        },
    )
    assert ai_settings.status_code == 200
    wishlist_id = _create_wishlist(client)
    source_id = _create_rss_source(client)

    response = client.post(
        "/api/v1/radar/run",
        json={"source_ids": [source_id], "wishlist_id": wishlist_id, "use_ai": True},
    )

    assert response.status_code == 200
    payload = response.json()
    result = payload["data"]["results"][0]
    assert result["analysis_mode"] == "ai"
    assert result["provider_used"] == "gemini"
    assert "Salvar na Caixa de Entrada para revisar." in result["next_actions"]
    serialized = json.dumps(payload).lower()
    assert FAKE_KEY.lower() not in serialized
    assert "api_key" not in serialized


def test_radar_invalid_rss_returns_friendly_source_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    def invalid_fetch(self, url: str, *, delay_seconds: float = 0.2) -> FetchResult:
        return FetchResult(
            url=url, status_code=200, content_type="application/rss+xml", text="<bad"
        )

    monkeypatch.setattr("modules.scraping.client.ScrapingClient.fetch", invalid_fetch)
    client = api_client()
    wishlist_id = _create_wishlist(client)
    source_id = _create_rss_source(client)

    response = client.post(
        "/api/v1/radar/run",
        json={"source_ids": [source_id], "wishlist_id": wishlist_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["run"]["total_errors"] == 1
    assert payload["data"]["results"] == []
