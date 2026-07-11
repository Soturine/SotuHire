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


def test_resume_tailor_reports_career_context_usage(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    profile = client.post(
        "/api/v1/profile/items",
        json={
            "type": "project",
            "title": "API FastAPI",
            "evidence": "Projeto de API com FastAPI e testes.",
            "confidence": "high",
        },
    )
    assert profile.status_code == 200

    response = client.post(
        "/api/v1/resume/tailor",
        json={
            "target_role": "Backend Python",
            "job_text": JOB_TEXT,
            "evidence_text": "Experiencia com Python.",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["context_evidence_count"] >= 1
    assert "API FastAPI" in payload["context_summary"]
    assert payload["prompt_id"] == "resume_tailor_v1"
    assert any(item["title"] == "API FastAPI" for item in payload["evidence_used"])


def test_resume_tailor_uses_academic_context_without_inventing_experience(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    profile = client.post(
        "/api/v1/profile/items",
        json={
            "type": "research_project",
            "title": "Projeto PIBIC em ionosfera",
            "evidence": "Projeto acadêmico de pesquisa com análise de dados em Python.",
            "source": "curriculum_lattes",
        },
    )
    assert profile.status_code == 200

    response = client.post(
        "/api/v1/resume/tailor",
        json={
            "target_role": "Estágio em pesquisa aplicada",
            "job_text": "Vaga pede pesquisa, Python e relatórios técnicos.",
            "evidence_text": "Sem experiência profissional formal.",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["context_evidence_count"] >= 1
    serialized = str(payload).lower()
    assert "projeto pibic em ionosfera" in serialized
    assert "invente" in serialized or "somente" in serialized or "verdade" in serialized
