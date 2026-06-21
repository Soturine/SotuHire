from modules.domain_intelligence import classify_domain, classify_requirement


def test_nursing_domain_detects_coren() -> None:
    result = classify_domain("Vaga para enfermeira de UTI com COREN ativo.")

    assert result.primary_domain.domain == "nursing"
    assert [signal.credential for signal in result.regulated_profession_signals] == ["COREN"]


def test_psychology_domain_detects_crp() -> None:
    result = classify_domain("Psicologo para RH com CRP ativo e avaliacao psicologica.")

    assert result.primary_domain.domain == "psychology"
    assert result.regulated_profession_signals[0].credential == "CRP"


def test_engineering_domain_detects_crea() -> None:
    result = classify_domain("Engenheiro civil com CREA para acompanhamento de obra.")

    assert result.primary_domain.domain in {"civil_engineering", "engineering"}
    assert result.regulated_profession_signals[0].credential == "CREA"


def test_architecture_domain_detects_cau() -> None:
    result = classify_domain("Arquiteta com CAU, Revit e SketchUp para projeto executivo.")

    assert result.primary_domain.domain == "architecture"
    assert result.regulated_profession_signals[0].credential == "CAU"


def test_pedagogy_domain_detects_bncc() -> None:
    result = classify_domain("Professor fundamental com Pedagogia, BNCC e alfabetizacao.")
    requirement = classify_requirement("BNCC")

    assert result.primary_domain.domain == "pedagogy"
    assert requirement.category == "regulation"


def test_cybersecurity_domain_detects_siem_and_soc() -> None:
    result = classify_domain("Analista SOC com SIEM, resposta a incidentes e hardening.")

    assert result.primary_domain.domain == "cybersecurity"
    assert {"SIEM", "SOC"}.issubset({alias.normalized_name for alias in result.aliases_detected})


def test_civil_engineering_domain_detects_autocad_and_revit() -> None:
    result = classify_domain("Engenharia civil de obras com AutoCAD, Revit e orcamento.")

    assert result.primary_domain.domain == "civil_engineering"
    assert {"AutoCAD", "Revit"}.issubset(
        {alias.normalized_name for alias in result.aliases_detected}
    )
