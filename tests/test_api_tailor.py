from tests.api_test_helpers import JOB_TEXT, RESUME_TEXT, api_client


def test_resume_tailor_returns_safe_reviewable_output() -> None:
    client = api_client()

    response = client.post(
        "/api/v1/resume/tailor",
        json={
            "target_role": "Backend Python",
            "target_company": "Empresa Ficticia",
            "job_text": JOB_TEXT,
            "evidence_text": RESUME_TEXT,
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["safe_to_export"] is True
    assert payload["tailor"]["target_role"] == "Backend Python"
    assert payload["tailor"]["warnings"]
