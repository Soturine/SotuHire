from tests.api_test_helpers import JOB_TEXT, RESUME_TEXT, api_client


def test_ats_analyze_separates_present_and_missing_keywords() -> None:
    client = api_client()

    response = client.post(
        "/api/v1/ats/analyze",
        json={
            "resume_text": RESUME_TEXT,
            "job_text": JOB_TEXT,
            "job_keywords": ["Python", "Docker"],
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["ats_score"] >= 0
    assert "Python" in payload["present"]
    assert "Docker" in (
        payload["missing_but_safe_to_add_if_true"] + payload["missing_without_evidence"]
    )
