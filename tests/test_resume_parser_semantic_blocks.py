from pathlib import Path

from modules.parsers.resume_parser import parse_resume_text

EXAMPLES = Path("examples/resumes")


def _engineering_resume():
    return parse_resume_text(
        (EXAMPLES / "rafael_like_engineering_resume.txt").read_text(encoding="utf-8")
    )


def test_experiences_are_grouped_as_semantic_blocks():
    profile = _engineering_resume()

    assert len(profile.experiences) == 2
    assert "Montagem e inspeção" in profile.experiences[0]
    assert "registro de não conformidades" in profile.experiences[0]
    assert "Preparação de sensores" in profile.experiences[1]


def test_projects_and_required_aliases_are_grouped():
    profile = _engineering_resume()

    assert len(profile.projects) == 2
    assert "Inclui comandos de histórico" in profile.projects[0]
    assert "O protótipo registra leituras" in profile.projects[1]
    assert "ESP32" in profile.skills
    assert profile.education
    assert profile.courses


def test_links_soft_skills_and_summary_are_normalized():
    profile = _engineering_resume()

    assert profile.linkedin == "linkedin.com/in/rafael-almeida-engenharia"
    assert profile.github == "github.com/rafael-almeida-labs"
    assert {"Trabalho em equipe", "comunicação técnica", "organização", "adaptabilidade"} <= set(
        profile.soft_skills
    )
    assert len(profile.summary) < len(profile.raw_text)
    assert profile.email not in profile.summary
    assert len(profile.summary.splitlines()) <= 3


def test_other_heading_aliases_are_recognized():
    data_profile = parse_resume_text(
        (EXAMPLES / "junior_data_resume.txt").read_text(encoding="utf-8")
    )
    web_profile = parse_resume_text(
        (EXAMPLES / "web_developer_resume.txt").read_text(encoding="utf-8")
    )

    assert len(data_profile.experiences) == 1
    assert len(data_profile.projects) == 2
    assert len(web_profile.experiences) == 1
    assert len(web_profile.projects) == 2
    assert "TypeScript" in web_profile.skills


def test_project_detail_labels_stay_in_the_current_block():
    profile = parse_resume_text(
        """
        Pessoa Exemplo
        PROJETOS SELECIONADOS
        Projeto Aurora: aplicação para organização de estudos.
        Tecnologias: Python, FastAPI e SQL.
        Projeto Farol: dashboard para acompanhamento de indicadores.
        """
    )

    assert len(profile.projects) == 2
    assert "Tecnologias: Python" in profile.projects[0]
