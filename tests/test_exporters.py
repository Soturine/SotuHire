import json

from modules.exporters.analysis_exporter import (
    analysis_to_json,
    analysis_to_markdown,
    save_export,
    tailor_to_markdown,
)
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput


def _analysis() -> JobAnalysisSchema:
    return JobAnalysisSchema(
        match_score=80,
        ats_score=75,
        opportunity_fit_score=90,
        risk_score=10,
        recommendation="apply",
        strengths=["Python"],
        gaps=["Cloud"],
        missing_keywords=["AWS"],
        tailored_summary="Pessoa desenvolvedora Python.",
    )


def test_json_export_is_valid():
    exported = analysis_to_json(_analysis())

    assert json.loads(exported)["recommendation"] == "apply"


def test_markdown_exports_contain_expected_sections():
    assert "# Analise SotuHire" in analysis_to_markdown(_analysis())
    tailor = ResumeTailorOutput(
        target_role="Backend",
        professional_summary="Pessoa desenvolvedora Python.",
        improved_bullets=["Desenvolveu API."],
        evidence_used=["Projeto de API."],
    )

    exported = tailor_to_markdown(tailor)

    assert "Bullet points melhorados" in exported
    assert "Evidencias usadas" in exported


def test_save_export_writes_inside_selected_directory(tmp_path):
    target = save_export('{"ok": true}', "analysis.json", tmp_path)

    assert target.read_text(encoding="utf-8") == '{"ok": true}'
