from pathlib import Path


def test_injected_modal_has_full_report_and_action_schema():
    script = Path("browser-extension/github_injected.js").read_text(encoding="utf-8")

    for expected in (
        "backdrop-filter:blur",
        "overall_score",
        "Grade",
        "Modelo:",
        "README",
        "Commits",
        "Arquitetura",
        "Pontos fortes",
        "Pontos fracos e inconsistencias",
        "Recomendacoes por prioridade",
        "Evidencias para curriculo",
        "Salvar no SotuHire",
        "Usar como evidencia em vaga",
        "Enviar para memoria",
        "Comparar com vaga atual",
        "Enviar para perfil profissional",
        "Exportar relatorio",
        "Copiar resumo",
        "Deep analysis",
    ):
        assert expected in script

    assert 'className = "report loading"' in script
    assert 'className = "report error"' in script
