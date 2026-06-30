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


def test_ats_uses_career_context_for_evidence_keywords(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    profile = client.post(
        "/api/v1/profile/items",
        json={
            "type": "technical_skill",
            "title": "Docker",
            "evidence": "Projeto local conteinerizado revisado pelo usuario.",
            "confidence": "high",
        },
    )
    assert profile.status_code == 200

    response = client.post(
        "/api/v1/ats/analyze",
        json={
            "resume_text": RESUME_TEXT,
            "job_text": JOB_TEXT,
            "job_keywords": ["Docker"],
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert "Docker" in payload["context_evidence_keywords"]
    assert any("Docker" in insight for insight in payload["ai_insights"])
