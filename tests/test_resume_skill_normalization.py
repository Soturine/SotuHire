from modules.parsers.resume_parser import parse_resume_text


def test_category_prefixes_and_normalized_duplicates_are_removed():
    profile = parse_resume_text(
        """
        Pessoa Exemplo
        COMPETENCIAS TECNICAS
        Linguagens: Java, Java, Python
        Web/Mobile: React / React
        Dados/DevOps/Ferramentas: MySQL, GitHub, REST
        Hardware/IoT: ESP32, MQTT
        Tecnologias: Python
        """
    )

    assert profile.skills == ["Java", "Python", "React", "MySQL", "GitHub", "REST", "ESP32", "MQTT"]
    assert not any(":" in skill for skill in profile.skills)


def test_soft_skills_do_not_enter_technical_skills():
    profile = parse_resume_text(
        """
        Pessoa Exemplo
        COMPETENCIAS TECNICAS
        Python, Trabalho em equipe, Comunicacao, Organizacao
        SOFT SKILLS
        Trabalho em equipe, comunicação, organização
        """
    )

    assert profile.skills == ["Python"]
    assert {"Trabalho em equipe", "comunicação", "organização"} <= set(profile.soft_skills)
