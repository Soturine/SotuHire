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
    capture = captures.json()["data"]["captures"][0]
    assert capture["id"] == "capture_demo"
    assert capture["kind"] == "job"
    assert capture["source"] == "browser_assisted_capture"
    assert capture["captured_at"]


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


def test_extension_bridge_reports_empty_local_companion_store(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    status = client.get("/api/v1/extension/status")
    captures = client.get("/api/v1/extension/captures")

    assert status.status_code == 200
    assert status.json()["data"]["available"] is True
    assert status.json()["data"]["capture_count"] == 0
    assert captures.status_code == 200
    assert captures.json()["data"]["captures"] == []


def test_extension_bridge_imports_fake_capture_to_tracker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_tracker",
            capture=BrowserCapturePayload(
                page_title="Backend Python Demo",
                url="https://example.invalid/jobs/backend",
                domain="example.invalid",
                visible_text="Cargo: Backend Python\nRequisitos: Python, FastAPI.",
                job_title="Backend Python Demo",
                company="Empresa Ficticia",
            ),
        )
    )
    client = api_client()

    response = client.post(
        "/api/v1/extension/import/tracker",
        json={"capture_id": "capture_tracker", "privacy_acknowledged": True},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["capture_id"] == "capture_tracker"
    assert payload["tracker_id"]
    assert payload["provider"] == "local"


def test_extension_bridge_imports_fake_github_capture(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_github",
            capture=BrowserCapturePayload(
                page_title="fictitious-api-lab",
                url="https://github.com/example/fictitious-api-lab",
                domain="github.com",
                visible_text="README FastAPI project with tests.",
                description="# Fictitious API\nFastAPI project with tests.",
            ),
        )
    )
    client = api_client()

    response = client.post("/api/v1/extension/import/github", json={"capture_id": "capture_github"})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["capture_id"] == "capture_github"
    assert payload["message"]
    assert payload["report"]


def test_extension_bridge_exposes_fake_github_capture_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_github_history",
            capture=BrowserCapturePayload(
                page_title="fictitious-api-lab",
                url="https://github.com/example/fictitious-api-lab",
                domain="github.com",
                visible_text="README FastAPI project with tests.",
                description="# Fictitious API\nFastAPI project with tests.",
            ),
        )
    )
    client = api_client()

    response = client.get("/api/v1/extension/captures")

    assert response.status_code == 200
    capture = response.json()["data"]["captures"][0]
    assert capture["kind"] == "github_repo"
    assert capture["source"] == "browser_assisted_capture"
    assert capture["url"] == "https://github.com/example/fictitious-api-lab"


def test_extension_context_endpoint_uses_career_context_engine(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.get("/api/v1/extension/context")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["context"]["purpose"] == "extension"
    assert "Contexto" in payload["message"]


def test_extension_profile_candidates_do_not_save_automatically(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_profile_candidate",
            capture=BrowserCapturePayload(
                page_title="Analista de Dados",
                url="https://example.invalid/jobs/data",
                domain="example.invalid",
                visible_text="Cargo: Analista de Dados\nRequisitos: Python, SQL. Local: Remoto.",
                job_title="Analista de Dados",
                company="Empresa Ficticia",
            ),
        )
    )
    client = api_client()

    candidates = client.post(
        "/api/v1/extension/captures/capture_profile_candidate/profile-candidates"
    )
    profile = client.get("/api/v1/profile")

    assert candidates.status_code == 200
    data = candidates.json()["data"]
    assert data["capture_id"] == "capture_profile_candidate"
    assert data["candidates"]
    assert data["candidates"][0]["confirmed_by_user"] is False
    assert profile.status_code == 200
    assert profile.json()["data"]["profile"]["items"] == []


def test_extension_add_to_profile_requires_user_confirmation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_add_profile",
            capture=BrowserCapturePayload(
                page_title="Backend Python Demo",
                url="https://example.invalid/jobs/backend",
                domain="example.invalid",
                visible_text="Cargo: Backend Python\nRequisitos: Python, FastAPI.",
                job_title="Backend Python Demo",
                company="Empresa Ficticia",
            ),
        )
    )
    client = api_client()
    candidates = client.post("/api/v1/extension/captures/capture_add_profile/profile-candidates")
    candidate_id = candidates.json()["data"]["candidates"][0]["item_id"]

    response = client.post(
        "/api/v1/extension/captures/capture_add_profile/add-to-profile",
        json={"candidate_ids": [candidate_id], "privacy_acknowledged": True},
    )
    profile = client.get("/api/v1/profile").json()["data"]["profile"]

    assert response.status_code == 200
    added = response.json()["data"]["added"]
    assert len(added) == 1
    assert added[0]["confirmed_by_user"] is True
    assert added[0]["source"] == "extension_capture"
    assert added[0]["source_ref"] == "capture_add_profile"
    assert profile["items"][0]["source_ref"] == "capture_add_profile"


def test_extension_github_capture_generates_project_profile_candidates(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    store = CompanionCaptureStore()
    store.save(
        CompanionCaptureRecord(
            id="capture_github_profile_candidate",
            capture=BrowserCapturePayload(
                page_title="fictitious-api-lab",
                url="https://github.com/example/fictitious-api-lab",
                domain="github.com",
                visible_text="README FastAPI project with Pytest and PostgreSQL.",
                description="# Fictitious API\nFastAPI project with Pytest and PostgreSQL.",
            ),
        )
    )
    client = api_client()

    response = client.post(
        "/api/v1/extension/projects/capture_github_profile_candidate/profile-candidates"
    )

    assert response.status_code == 200
    candidates = response.json()["data"]["candidates"]
    assert any(item["type"] == "project" for item in candidates)
    assert {item["source"] for item in candidates} == {"github_capture"}
