from __future__ import annotations

import json
from pathlib import Path

from modules.local_api import BrowserCapturePayload, CompanionCaptureRecord, CompanionCaptureStore
from modules.scraping.schemas import FetchResult
from tests.api_test_helpers import api_client

JOB_TEXT = """Cargo: Analista de Dados
Empresa: Empresa Exemplo
Localizacao: Remoto
Requisitos: Python, SQL e dashboards.
"""


def test_source_import_text_persists_inbox_item(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post(
        "/api/v1/sources/imports/text",
        json={
            "text": JOB_TEXT,
            "title": "Analista de Dados",
            "company": "Empresa Exemplo",
            "url": "https://example.com/jobs/123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["batch"]["imported"] == 1
    item = payload["data"]["items"][0]
    assert item["origin"] == "manual_text"
    assert item["title"] == "Analista de Dados"
    assert "api_key" not in json.dumps(payload)

    inbox = client.get("/api/v1/sources/imports")
    assert inbox.status_code == 200
    assert inbox.json()["data"]["items"][0]["job_url"] == "https://example.com/jobs/123"


def test_source_import_url_uses_mocked_public_fetch(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    def fake_fetch(self, url: str, *, delay_seconds: float = 0.2) -> FetchResult:
        return FetchResult(
            url=url,
            status_code=200,
            content_type="text/html",
            text=(
                "<html><title>Desenvolvedor Backend</title><body>"
                "Cargo: Desenvolvedor Backend Empresa: Tech Exemplo "
                "Requisitos: Python, APIs e testes."
                "</body></html>"
            ),
        )

    monkeypatch.setattr("modules.sources.imports.ScrapingClient.fetch", fake_fetch)
    client = api_client()

    response = client.post(
        "/api/v1/sources/imports/url",
        json={"url": "https://example.com/jobs/456"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["warnings"] == []
    assert payload["data"]["items"][0]["origin"] == "manual_url"
    assert payload["data"]["items"][0]["job_url"] == "https://example.com/jobs/456"


def test_source_import_url_blocked_guides_manual_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    def blocked_fetch(self, url: str, *, delay_seconds: float = 0.2) -> FetchResult:
        raise PermissionError("login requerido")

    monkeypatch.setattr("modules.sources.imports.ScrapingClient.fetch", blocked_fetch)
    client = api_client()

    response = client.post(
        "/api/v1/sources/imports/url",
        json={"url": "https://example.com/private/jobs/789"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["warnings"]
    assert "cole o texto da vaga manualmente" in payload["warnings"][0]
    assert payload["data"]["items"][0]["status"] == "error"


def test_source_import_with_ai_flag_uses_local_fallback_without_secret(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post(
        "/api/v1/sources/imports/text",
        json={
            "text": JOB_TEXT,
            "title": "Analista de Dados",
            "company": "Empresa Exemplo",
            "use_ai": True,
        },
    )

    payload = response.json()
    serialized = json.dumps(payload).lower()
    assert response.status_code == 200
    assert payload["warnings"]
    assert "extracao local" in payload["warnings"][0]
    assert payload["data"]["items"][0]["origin"] == "manual_text"
    assert "api_key" not in serialized
    assert "secret" not in serialized


def test_source_import_csv_valid_missing_fields_and_dedupe(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    csv_text = """cargo,empresa,link,local,descricao,fonte,status,observacoes
Analista de Dados,Empresa Exemplo,https://example.com/jobs/123,Remoto,"Python, SQL e dashboards",CSV Manual,nova,"vaga ficticia"
Desenvolvedor Backend,Tech Exemplo,https://example.com/jobs/456,Hibrido,"APIs, testes e bancos de dados",CSV Manual,nova,"vaga ficticia"
,Empresa Sem Cargo,,Remoto,,CSV Manual,nova,"faltando cargo"
"""

    response = client.post("/api/v1/sources/imports/csv", json={"csv_text": csv_text})
    duplicate = client.post(
        "/api/v1/sources/imports/text",
        json={
            "text": JOB_TEXT,
            "title": "Analista de Dados",
            "company": "Empresa Exemplo",
            "url": "https://example.com/jobs/123?utm=demo",
        },
    )
    dedupe = client.post("/api/v1/sources/dedupe")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["batch"]["imported"] == 2
    assert payload["data"]["batch"]["errors"] == 1
    assert payload["warnings"]
    assert duplicate.status_code == 200
    assert duplicate.json()["data"]["batch"]["duplicates"] == 1
    assert dedupe.status_code == 200
    assert dedupe.json()["data"]["duplicates"]


def test_source_import_json_valid_and_invalid(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    valid = client.post(
        "/api/v1/sources/imports/json",
        json={
            "items": [
                {
                    "cargo": "Analista de Dados",
                    "empresa": "Empresa Exemplo",
                    "link": "https://example.com/jobs/123",
                    "local": "Remoto",
                    "descricao": "Python, SQL e dashboards.",
                    "fonte": "JSON Manual",
                    "observacoes": "vaga ficticia",
                }
            ]
        },
    )
    invalid = client.post("/api/v1/sources/imports/json", json={"json_text": "{bad"})

    assert valid.status_code == 200
    assert valid.json()["data"]["batch"]["imported"] == 1
    assert invalid.status_code == 422


def test_source_capture_actions_stats_and_tracker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    created = client.post(
        "/api/v1/sources/imports/text",
        json={"text": JOB_TEXT, "title": "Analista de Dados", "company": "Empresa Exemplo"},
    )
    item_id = created.json()["data"]["items"][0]["id"]

    reviewed = client.patch(f"/api/v1/sources/captures/{item_id}", json={"status": "reviewed"})
    imported = client.post(f"/api/v1/sources/captures/{item_id}/import-job")
    saved = client.post(f"/api/v1/sources/captures/{item_id}/save-tracker")
    stats = client.get("/api/v1/sources/stats")

    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["capture"]["status"] == "reviewed"
    assert imported.status_code == 200
    assert imported.json()["data"]["job"]["title"] == "Analista de Dados"
    assert saved.status_code == 200
    assert saved.json()["data"]["tracker_id"]
    assert stats.status_code == 200
    assert stats.json()["data"]["saved_to_tracker"] == 1


def test_extension_capture_patch_marks_reviewed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_patch",
            capture=BrowserCapturePayload(
                page_title="Backend Python Demo",
                url="https://example.invalid/jobs/backend",
                visible_text="Vaga ficticia para Backend Python.",
            ),
        )
    )
    client = api_client()

    response = client.patch(
        "/api/v1/extension/captures/capture_patch",
        json={"status": "archived"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["capture"]["status"] == "archived"
