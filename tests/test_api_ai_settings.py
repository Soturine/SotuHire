from __future__ import annotations

import json
from pathlib import Path

from tests.api_test_helpers import api_client

FAKE_KEY = "test-provider-local-key"


def test_ai_settings_default_status_is_safe(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.get("/api/v1/settings/ai")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["provider"] == "local"
    assert payload["data"]["configured"] is True
    assert payload["data"]["allow_resume"] is True
    assert payload["data"]["allow_job"] is True
    assert payload["data"]["allow_source_import"] is True
    assert payload["data"]["allow_radar"] is True
    assert "api_key" not in json.dumps(payload)


def test_ai_settings_save_gemini_key_backend_side_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post(
        "/api/v1/settings/ai",
        json={
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "api_key": FAKE_KEY,
            "use_ai": True,
            "allow_resume": True,
            "allow_job": True,
            "allow_match": True,
            "allow_ats": True,
            "allow_tailor": True,
            "allow_github": False,
            "allow_source_import": True,
            "allow_radar": False,
            "allow_memory_context": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["provider"] == "gemini"
    assert payload["data"]["configured"] is True
    assert payload["data"]["allow_radar"] is False
    assert payload["data"]["allow_public_exams"] is True
    assert FAKE_KEY not in json.dumps(payload)
    assert "api_key" not in json.dumps(payload)

    settings_file = tmp_path / "settings" / "ai-settings.json"
    secret_file = tmp_path / "secrets" / "ai-provider.local.json"
    assert settings_file.exists()
    assert secret_file.exists()
    assert FAKE_KEY not in settings_file.read_text(encoding="utf-8")
    assert FAKE_KEY in secret_file.read_text(encoding="utf-8")

    status = client.get("/api/v1/settings/ai/status").json()
    assert status["data"]["configured"] is True
    assert FAKE_KEY not in json.dumps(status)


def test_ai_settings_delete_removes_secret(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    client.post(
        "/api/v1/settings/ai",
        json={"provider": "gemini", "model": "gemini-2.5-flash", "api_key": FAKE_KEY},
    )

    response = client.delete("/api/v1/settings/ai")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["configured"] is False
    assert FAKE_KEY not in json.dumps(payload)
    assert not (tmp_path / "secrets" / "ai-provider.local.json").exists()


def test_ai_settings_test_local_without_external_call(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post("/api/v1/settings/ai/test", json={"provider": "local"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["success"] is True
    assert payload["data"]["provider"] == "local"


def test_ai_settings_test_gemini_missing_key_is_friendly(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post("/api/v1/settings/ai/test", json={"provider": "gemini"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["success"] is False
    assert payload["data"]["status"] == "not_configured"
    assert FAKE_KEY not in json.dumps(payload)


def test_ai_settings_lists_providers_and_builtin_models_without_secrets(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    client.post(
        "/api/v1/settings/ai",
        json={"provider": "gemini", "model": "gemini-2.5-flash", "api_key": FAKE_KEY},
    )

    providers = client.get("/api/v1/settings/ai/providers")
    gemini_models = client.get("/api/v1/settings/ai/models?provider=gemini")
    openai_models = client.get("/api/v1/settings/ai/models?provider=openai")

    assert providers.status_code == 200
    assert {item["id"] for item in providers.json()["data"]["providers"]} >= {
        "local",
        "gemini",
        "openai",
    }
    assert any(
        model["id"] == "gemini-2.5-flash" for model in gemini_models.json()["data"]["models"]
    )
    assert any(model["id"] == "gpt-5-mini" for model in openai_models.json()["data"]["models"])
    serialized = json.dumps([providers.json(), gemini_models.json(), openai_models.json()])
    assert FAKE_KEY not in serialized
    assert '"api_key":' not in serialized


def test_ai_settings_refresh_models_without_key_keeps_builtin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post("/api/v1/settings/ai/models/refresh", json={"provider": "openai"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["provider"] == "openai"
    assert payload["data"]["models"]
    assert payload["warnings"]


def test_ai_settings_openai_provider_saves_tests_and_uses_model(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class FakeOpenAIProvider:
        name = "openai"

        def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
            self.api_key = api_key or ""
            self.model = model or "gpt-5-mini"

        def ping(self) -> str:
            assert self.api_key == FAKE_KEY
            return "ok"

    monkeypatch.setattr("apps.api.services.ai_settings.OpenAIProvider", FakeOpenAIProvider)
    client = api_client()

    saved = client.post(
        "/api/v1/settings/ai",
        json={
            "provider": "openai",
            "model": "gpt-5-mini",
            "api_key": FAKE_KEY,
            "use_ai": True,
            "allow_public_exams": True,
        },
    )
    tested = client.post("/api/v1/settings/ai/test", json={"provider": "openai"})

    assert saved.status_code == 200
    assert saved.json()["data"]["provider"] == "openai"
    assert saved.json()["data"]["configured"] is True
    assert FAKE_KEY not in json.dumps(saved.json())
    assert tested.status_code == 200
    assert tested.json()["data"]["success"] is True
    assert tested.json()["data"]["model"] == "gpt-5-mini"


def test_ai_settings_openai_future_alias_migrates_safely(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    response = client.post(
        "/api/v1/settings/ai",
        json={"provider": "openai_future", "model": "gpt-5-mini", "use_ai": True},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["provider"] == "openai"
    assert payload["status"] == "not_configured"
    assert "planned" not in json.dumps(payload).lower()
