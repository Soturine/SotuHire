from tests.api_test_helpers import JOB_TEXT, api_client


def test_job_extract_returns_structured_job_without_raw_text_by_default() -> None:
    client = api_client()

    response = client.post("/api/v1/job/extract", json={"job_text": JOB_TEXT})

    assert response.status_code == 200
    payload = response.json()
    job = payload["data"]["job"]
    assert payload["ok"] is True
    assert job["title"] == "Desenvolvedor Backend Python"
    assert "Python" in job["required_skills"]
    assert job["raw_text"] == ""


def test_job_extract_returns_validation_error_for_empty_payload() -> None:
    client = api_client()

    response = client.post("/api/v1/job/extract", json={"job_text": ""})

    assert response.status_code == 422
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_payload"
