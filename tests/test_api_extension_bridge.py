from __future__ import annotations

from pathlib import Path

from modules.local_api import BrowserCapturePayload, CompanionCaptureRecord, CompanionCaptureStore
from tests.api_test_helpers import api_client


def test_extension_bridge_lists_local_companion_captures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_demo",
            capture=BrowserCapturePayload(
                page_title="Backend Python Demo",
                url="https://example.invalid/jobs/backend",
                domain="example.invalid",
                visible_text="Vaga ficticia para Backend Python com FastAPI.",
                job_title="Backend Python Demo",
                company="Empresa Ficticia",
            ),
        )
    )
    client = api_client()

    status = client.get("/api/v1/extension/status")
    captures = client.get("/api/v1/extension/captures")

    assert status.status_code == 200
    assert status.json()["data"]["capture_count"] == 1
    assert captures.status_code == 200
    assert captures.json()["data"]["captures"][0]["id"] == "capture_demo"


def test_extension_bridge_imports_capture_as_job(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_job",
            capture=BrowserCapturePayload(
                page_title="Desenvolvedor Backend Python",
                url="https://example.invalid/jobs/backend",
                domain="example.invalid",
                visible_text="Cargo: Desenvolvedor Backend Python\nRequisitos: Python, FastAPI.",
                job_title="Desenvolvedor Backend Python",
                company="Empresa Ficticia",
            ),
        )
    )
    client = api_client()

    response = client.post("/api/v1/extension/import/job", json={"capture_id": "capture_job"})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["job"]["title"] == "Desenvolvedor Backend Python"
    assert payload["capture_id"] == "capture_job"
