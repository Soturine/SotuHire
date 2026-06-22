from tests.api_test_helpers import JOB_TEXT, RESUME_TEXT, api_client


def test_match_analyze_uses_local_match_engine() -> None:
    client = api_client()

    response = client.post(
        "/api/v1/match/analyze",
        json={"resume_text": RESUME_TEXT, "job_text": JOB_TEXT},
    )

    assert response.status_code == 200
    payload = response.json()
    analysis = payload["data"]["analysis"]
    assert payload["data"]["provider_used"] == "local"
    assert analysis["match_score"] >= 0
    assert analysis["analysis_version"] == "match_engine_v2"


def test_match_analyze_requires_resume_and_job_context() -> None:
    client = api_client()

    response = client.post("/api/v1/match/analyze", json={"resume_text": RESUME_TEXT})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "http_error"
