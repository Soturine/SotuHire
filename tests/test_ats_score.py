from modules.ats.ats_score import analyze_ats_issues, calculate_simple_ats_score
from modules.ats.match_keywords import review_keywords_with_match
from modules.schemas.job_analysis import JobAnalysisSchema


def test_ats_score_accepts_empty_text_without_breaking():
    assert calculate_simple_ats_score("", "") == 0
    assert analyze_ats_issues("", "") == ["Curriculo vazio."]


def test_ats_score_rewards_clear_sections_and_keyword_coverage():
    resume = """
    Resumo profissional com Python, SQL e APIs.
    Experiencia
    Desenvolvimento de APIs em Python e consultas SQL.
    Projetos
    API com testes automatizados e documentacao.
    Educacao
    Graduacao em tecnologia.
    """
    job = "Pessoa desenvolvedora Python com SQL, APIs, testes e documentacao."

    assert calculate_simple_ats_score(resume, job) >= 65


def test_ats_score_detects_simple_formatting_and_content_problems():
    resume = "Nome\tTelefone\tEmail\tObjetivo curto │ sem secoes"
    job = "Python SQL testes APIs"

    issues = analyze_ats_issues(resume, job)

    assert calculate_simple_ats_score(resume, job) < 60
    assert len(issues) >= 3


def test_ats_keyword_review_uses_match_engine_evidence():
    analysis = JobAnalysisSchema(
        match_score=72,
        ats_score=70,
        opportunity_fit_score=60,
        risk_score=10,
        recommendation="apply_with_adjustments",
        analysis_version="match_engine_v2",
        matched_requirements=["Python"],
        partial_requirements=["Docker"],
        missing_requirements=["AWS"],
        evidence_used=["resume: Python"],
        ats_present_keywords=["Python"],
        ats_missing_but_safe_to_add=["Docker"],
        ats_missing_without_evidence=["AWS"],
    )

    review = review_keywords_with_match(analysis, ["Python", "Docker", "AWS"])

    assert review.present == ["Python"]
    assert review.missing_but_safe_to_add_if_true == ["Docker"]
    assert review.missing_without_evidence == ["AWS"]
