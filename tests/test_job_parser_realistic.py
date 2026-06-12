from modules.parsers.job_description_parser import parse_job_description


def test_realistic_job_detects_core_fields_skills_and_benefits():
    parsed = parse_job_description(
        """
        Cargo: Desenvolvedor Backend Júnior
        Empresa: Acme Tech
        Localização: São Paulo/SP
        Vaga remota com contrato CLT.
        Requisitos obrigatórios: Python, FastAPI, PostgreSQL e inglês fluente obrigatório.
        Desejável: Docker e AWS.

        Benefícios: plano de saúde, vale-refeição e Gympass.
        """
    )

    assert parsed.title == "Desenvolvedor Backend Júnior"
    assert parsed.company == "Acme Tech"
    assert parsed.location == "São Paulo/SP"
    assert parsed.modality == "remote"
    assert parsed.seniority == "junior"
    assert parsed.contract == "CLT"
    assert {"Python", "FastAPI", "PostgreSQL"} <= set(parsed.required_skills)
    assert {"Docker", "AWS"} <= set(parsed.desired_skills)
    assert parsed.english_required
    assert {"Plano de saúde", "Vale-refeição", "Gympass/Wellhub"} <= set(parsed.benefits)


def test_job_parser_reports_missing_important_data():
    parsed = parse_job_description("Analista de Dados Júnior remoto com Python e SQL")

    assert parsed.modality == "remote"
    assert parsed.seniority == "junior"
    assert "Empresa não informada." in parsed.risk_flags
    assert "Tipo de contrato não informado." in parsed.risk_flags
    assert "Faixa salarial não informada." in parsed.risk_flags


def test_empty_job_is_safe_and_reports_empty_description():
    parsed = parse_job_description("")

    assert parsed.raw_text == ""
    assert parsed.risk_flags == ["Descrição da vaga vazia."]
