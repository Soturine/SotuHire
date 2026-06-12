from modules.parsers.resume_parser import parse_resume_text

REALISTIC_RESUME = """
Rafael Ryan Ramos de Souza
Jacareí, SP | +55 (12) 98297-7845 | souzaramos2001@gmail.com
LinkedIn: linkedin.com/in/rafaelryansouza | GitHub: github.com/Soturine

OBJETIVO
Estágio ou posição júnior em Engenharia da Computação.

RESUMO PROFISSIONAL
Técnico em Mecatrônica e estudante de Engenharia da Computação com experiência em automação.

FORMAÇÃO
Técnico em Mecatrônica - ETEC
Engenharia da Computação - UNIVAP

EXPERIÊNCIA PROFISSIONAL
Estágio na Embraer com instrumentação e aquisição de dados.

PROJETOS ACADÊMICOS
Projeto acadêmico de sistema IoT com ESP32, MQTT, Node.js e React.

SKILLS
Python, Java, React, Docker, SQL, Python

SOFT SKILLS
Comunicação, organização e trabalho em equipe

IDIOMAS
Inglês intermediário
"""


def test_realistic_resume_detects_contact_links_and_sections():
    parsed = parse_resume_text(REALISTIC_RESUME)

    assert parsed.name == "Rafael Ryan Ramos de Souza"
    assert parsed.email == "souzaramos2001@gmail.com"
    assert parsed.phone == "+55 (12) 98297-7845"
    assert parsed.city == "Jacareí/SP"
    assert parsed.linkedin == "linkedin.com/in/rafaelryansouza"
    assert parsed.github == "github.com/Soturine"
    assert {"linkedin.com/in/rafaelryansouza", "github.com/Soturine"} <= set(parsed.links)
    assert any("Técnico em Mecatrônica" in item for item in parsed.education)
    assert any("Estágio" in item for item in parsed.experiences)
    assert any("Projeto acadêmico" in item for item in parsed.projects)


def test_realistic_resume_skills_are_unique_and_summary_is_bounded():
    parsed = parse_resume_text(REALISTIC_RESUME)

    assert parsed.skills.count("Python") == 1
    assert len(parsed.skills) == len(set(parsed.skills))
    assert parsed.summary
    assert len(parsed.summary) <= 600
    assert len(parsed.summary) < len(parsed.raw_text)
    assert "LinkedIn" not in parsed.summary


def test_resume_without_headings_still_infers_education_experience_and_project():
    parsed = parse_resume_text(
        """
        Ana Souza
        Técnico em Mecatrônica pela ETEC
        Estágio em manutenção e automação industrial
        Projeto acadêmico de monitoramento com Python
        """
    )

    assert any("Técnico em Mecatrônica" in item for item in parsed.education)
    assert any("Estágio" in item for item in parsed.experiences)
    assert any("Projeto acadêmico" in item for item in parsed.projects)
