from tests.api_test_helpers import api_client


def test_health_returns_version_capabilities_and_restricted_cors() -> None:
    client = api_client()

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["version"] == "1.9.6"
    assert "resume_extract" in payload["data"]["capabilities"]
    assert "universal_career_profile" in payload["data"]["capabilities"]
    assert "authenticated_assisted_capture" in payload["data"]["capabilities"]
    assert "scheduled_radar" in payload["data"]["capabilities"]
    assert "local_notifications" in payload["data"]["capabilities"]
    assert "public_exams_foundation" in payload["data"]["capabilities"]
    assert "*" not in payload["data"]["cors_allowed_origins"]


def test_openapi_exposes_api_v1_contract() -> None:
    client = api_client()

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/settings/ai" in paths
    assert "/api/v1/settings/ai/status" in paths
    assert "/api/v1/settings/ai/providers" in paths
    assert "/api/v1/settings/ai/models" in paths
    assert "/api/v1/settings/ai/models/refresh" in paths
    assert "/api/v1/settings/ai/test" in paths
    assert "/api/v1/profile" in paths
    assert "/api/v1/profile/items" in paths
    assert "/api/v1/profile/import-text" in paths
    assert "/api/v1/profile/deduplicate" in paths
    assert "/api/v1/profile/context" in paths
    assert "/api/v1/sources/authenticated-captures" in paths
    assert "/api/v1/tracker/jobs" in paths
    assert "/api/v1/radar/wishlists" in paths
    assert "/api/v1/radar/wishlists/draft" in paths
    assert "/api/v1/radar/sources" in paths
    assert "/api/v1/radar/run" in paths
    assert "/api/v1/radar/results" in paths
    assert "/api/v1/radar/alerts" in paths
    assert "/api/v1/radar/stats" in paths
    assert "/api/v1/radar/schedules" in paths
    assert "/api/v1/radar/schedules/{schedule_id}/run-now" in paths
    assert "/api/v1/radar/scheduled-runs" in paths
    assert "/api/v1/radar/scheduler/status" in paths
    assert "/api/v1/notifications" in paths
    assert "/api/v1/notifications/mark-all-read" in paths
    assert "/api/v1/public-exams/import" in paths
    assert "/api/v1/public-exams" in paths
    assert "/api/v1/public-exams/{notice_id}/confirm" in paths
    assert "/api/v1/public-exams/{notice_id}/analyze" in paths
    assert "/api/v1/public-exams/{notice_id}/study-plan" in paths
    assert "/api/v1/extension/import/public-exam" in paths
