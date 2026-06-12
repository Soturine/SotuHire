from modules.parsers.job_description_parser import parse_job_description


def test_job_parser_accepts_empty_text():
    parsed = parse_job_description("")

    assert parsed.title == ""
    assert parsed.modality == "unknown"
    assert parsed.required_skills == []


def test_job_parser_detects_common_vacancy_fields():
    parsed = parse_job_description(
        """
        Cargo: Analista de Dados Junior
        Empresa: Acme Tech
        Localizacao: Sao Paulo
        Modelo hibrido, contrato CLT, salario R$ 5.000 a R$ 7.000.
        Requisitos: Python, SQL, Power BI e ingles fluente obrigatorio.
        Desejavel: AWS e Docker.
        """
    )

    assert parsed.title == "Analista de Dados Junior"
    assert parsed.company == "Acme Tech"
    assert parsed.location == "Sao Paulo"
    assert parsed.modality == "hybrid"
    assert parsed.seniority == "junior"
    assert parsed.contract == "CLT"
    assert parsed.salary_min == 5000
    assert parsed.salary_max == 7000
    assert {"Python", "SQL", "Power BI"} <= set(parsed.required_skills)
    assert {"AWS", "Docker"} <= set(parsed.desired_skills)
    assert parsed.english_required


def test_job_parser_detects_remote_senior_role():
    parsed = parse_job_description("Senior Python Developer remoto com FastAPI e PostgreSQL")

    assert parsed.modality == "remote"
    assert parsed.seniority == "senior"
    assert {"Python", "FastAPI", "PostgreSQL"} <= set(parsed.required_skills)
    assert parsed.salary_min is None
