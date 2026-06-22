from tests.api_test_helpers import RESUME_TEXT, api_client


def test_resume_extract_returns_structured_profile_without_raw_text_by_default() -> None:
    client = api_client()

    response = client.post("/api/v1/resume/extract", json={"resume_text": RESUME_TEXT})

    assert response.status_code == 200
    payload = response.json()
    profile = payload["data"]["profile"]
    assert payload["ok"] is True
    assert "Python" in profile["skills"]
    assert profile["raw_text"] == ""
    assert payload["data"]["confidence"] > 0.5


def test_resume_extract_can_echo_raw_text_when_explicit() -> None:
    client = api_client()

    response = client.post(
        "/api/v1/resume/extract",
        json={"resume_text": RESUME_TEXT, "include_raw_text": True},
    )

    assert response.status_code == 200
    assert "Pessoa Ficticia" in response.json()["data"]["profile"]["raw_text"]
