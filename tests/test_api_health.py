from tests.api_test_helpers import api_client


def test_health_returns_version_capabilities_and_restricted_cors() -> None:
    client = api_client()

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["version"] == "1.7.1"
    assert "resume_extract" in payload["data"]["capabilities"]
    assert "*" not in payload["data"]["cors_allowed_origins"]


def test_openapi_exposes_api_v1_contract() -> None:
    client = api_client()

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/settings/ai" in paths
    assert "/api/v1/settings/ai/status" in paths
    assert "/api/v1/settings/ai/test" in paths
    assert "/api/v1/tracker/jobs" in paths
