from modules.ats.ats_score import analyze_ats_issues, calculate_simple_ats_score


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
