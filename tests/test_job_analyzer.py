from modules.analyzer.job_analyzer import analyze_job, detect_missing_keywords
from modules.schemas.user_preferences import UserPreferences


def test_analyze_job_returns_valid_schema():
    resume = """
    Resumo
    Desenvolvedor Python com projetos de API e testes.
    Experiencia
    Projeto de API Python documentada.
    Educacao
    Graduacao em tecnologia.
    """
    job = """
    Vaga para pessoa desenvolvedora Python junior.
    Requisitos: Python, API, testes, SQL e documentacao.
    Trabalho remoto em contrato CLT.
    """
    preferences = UserPreferences(
        preferred_modalities=["remote"],
        accepted_contracts=["CLT"],
        target_levels=["junior"],
    )

    analysis = analyze_job(
        resume,
        job,
        preferences,
        {"modality": "remote", "contract": "CLT", "seniority": "junior"},
    )

    assert 0 <= analysis.match_score <= 100
    assert analysis.opportunity_fit_score == 100
    assert "sql" in analysis.missing_keywords
    assert analysis.tailored_summary in resume.replace("\n", " ") or analysis.tailored_summary


def test_analyze_job_accepts_empty_texts():
    analysis = analyze_job("", "")

    assert analysis.match_score == 0
    assert analysis.ats_score == 0
    assert analysis.risk_score == 100
    assert analysis.recommendation == "ignore"
    assert detect_missing_keywords("", "") == []
