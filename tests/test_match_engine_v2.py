from pathlib import Path
from typing import Any

from modules.ai.schemas.job_extraction import JobExtractionOutput
from modules.ai.schemas.resume_extraction import ResumeExtractionOutput
from modules.analyzer.job_analyzer import analyze_job_v2
from modules.github_analyzer.schemas import GitHubAnalyzerReport
from modules.matching.engine import analyze_match_v2

FIXTURES = Path("tests/fixtures/matching")


def _resume(name: str) -> ResumeExtractionOutput:
    return ResumeExtractionOutput.model_validate_json((FIXTURES / name).read_text(encoding="utf-8"))


def _job(name: str) -> JobExtractionOutput:
    return JobExtractionOutput.model_validate_json((FIXTURES / name).read_text(encoding="utf-8"))


def _github(name: str) -> GitHubAnalyzerReport:
    return GitHubAnalyzerReport.model_validate_json((FIXTURES / name).read_text(encoding="utf-8"))


def test_match_engine_v2_runs_without_real_ai_and_uses_github_evidence() -> None:
    result = analyze_match_v2(
        resume=_resume("resume_dev_backend.json"),
        job=_job("job_dev_backend.json"),
        github_report=_github("github_evidence_backend.json"),
        preferences_fit_score=80,
    )

    assert result.provider_used == "local"
    assert result.fallback_used is False
    assert result.score_breakdown.overall_score >= 60
    assert result.score_breakdown.portfolio_github_evidence_score > 0
    assert any("FastAPI" in item for item in result.explanation.evidence_used)


def test_match_engine_v2_matches_regulated_resume_when_license_is_present() -> None:
    result = analyze_match_v2(
        resume=_resume("resume_enfermagem.json"),
        job=_job("job_enfermeiro_uti.json"),
    )

    assert any(match.requirement.normalized_name == "COREN" for match in result.requirement_matches)
    assert not any(gap.requirement.normalized_name == "COREN" for gap in result.critical_gaps)
    assert result.score_breakdown.overall_score > 40


def test_match_engine_v2_marks_missing_required_professional_license_as_critical() -> None:
    resume = _resume("resume_engenharia_civil.json").model_copy(
        update={"professional_licenses": []}
    )
    result = analyze_match_v2(
        resume=resume,
        job=_job("job_engenheiro_civil_obras.json"),
    )

    assert any(gap.requirement.normalized_name == "CREA" for gap in result.critical_gaps)
    assert result.score_breakdown.overall_score <= 40
    assert result.recommendation == "ignore"


def test_legacy_analysis_fallback_still_works(monkeypatch: Any) -> None:
    def fail_match_engine(**kwargs: object) -> None:
        raise RuntimeError("engine unavailable")

    monkeypatch.setattr("modules.matching.engine.analyze_match_v2", fail_match_engine)

    analysis = analyze_job_v2(
        resume=_resume("resume_dev_backend.json"),
        job=_job("job_dev_backend.json"),
        fallback_resume_text="Python FastAPI PostgreSQL",
        fallback_job_text="Python FastAPI PostgreSQL",
    )

    assert analysis.match_score > 0
    assert analysis.recommendation
