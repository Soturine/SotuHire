from modules.resume_tailor.keyword_helper import suggest_safe_keywords
from modules.resume_tailor.section_ranker import rank_resume_sections
from modules.resume_tailor.tailor_rules import build_safe_tailor_output


def test_suggest_safe_keywords_only_returns_evidence_backed_terms():
    suggestions = suggest_safe_keywords(
        ["Python", "SQL", "Power BI"],
        "Projeto de API em Python com consultas SQL.",
    )

    assert suggestions == ["Python", "SQL"]


def test_suggest_safe_keywords_avoids_substring_false_positive():
    assert suggest_safe_keywords(["SQL"], "Projeto usando banco NoSQL.") == []


def test_rank_resume_sections_prioritizes_relevant_projects():
    ranked = rank_resume_sections(
        "Vaga Python com GitHub, projetos e portfolio.",
        ["Educacao", "Projetos", "Experiencia"],
    )

    assert ranked[0] == "Projetos"


def test_safe_tailor_output_never_invents_information():
    output = build_safe_tailor_output(
        target_role="Analista de Dados",
        job_text="Python SQL Power BI dashboards",
        evidence_text="Resumo. Projeto academico em Python e SQL.",
    )

    assert output.is_safe_to_export()
    assert all(not section.invented_information for section in output.tailored_sections)
    assert "power" not in output.keywords_added
    assert any("sem evidencia" in warning for warning in output.warnings)
    assert output.professional_summary
    assert output.improved_bullets
    assert output.evidence_used


def test_safe_tailor_output_accepts_empty_texts():
    output = build_safe_tailor_output("Cargo alvo", "", "")

    assert output.is_safe_to_export()
    assert output.tailored_sections == []
    assert output.warnings
