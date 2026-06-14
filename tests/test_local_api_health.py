from modules.local_api import LocalCompanionApp


def test_local_api_health_does_not_expose_gemini_key():
    status, payload = LocalCompanionApp().handle("GET", "/health")

    assert status == 200
    assert payload["ok"] is True
    assert "GEMINI" not in str(payload).upper()
