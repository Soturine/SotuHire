from pathlib import Path

from modules.ai.schemas.resume_extraction import ResumeExtractionOutput
from modules.github_analyzer.schemas import GitHubAnalyzerReport
from modules.matching.evidence_matcher import (
    collect_github_evidence,
    collect_resume_evidence,
    collect_text_evidence,
    combine_evidence,
)

FIXTURES = Path("tests/fixtures/matching")


def test_collect_resume_evidence_includes_professional_license() -> None:
    resume = ResumeExtractionOutput.model_validate_json(
        (FIXTURES / "resume_enfermagem.json").read_text(encoding="utf-8")
    )

    evidence = collect_resume_evidence(resume)

    coren = next(item for item in evidence if item.normalized_name == "COREN")
    assert coren.category == "professional_license"
    assert coren.evidence_source == "resume"
    assert coren.confidence >= 0.9


def test_collect_github_evidence_maps_repository_signals() -> None:
    report = GitHubAnalyzerReport.model_validate_json(
        (FIXTURES / "github_evidence_backend.json").read_text(encoding="utf-8")
    )

    evidence = collect_github_evidence(report)

    assert any(
        item.normalized_name.casefold() == "fastapi" and item.evidence_source == "github"
        for item in evidence
    )
    assert any("modules/api.py" in item.evidence_file for item in evidence)


def test_combine_evidence_keeps_distinct_sources() -> None:
    resume = ResumeExtractionOutput.model_validate_json(
        (FIXTURES / "resume_dev_backend.json").read_text(encoding="utf-8")
    )
    report = GitHubAnalyzerReport.model_validate_json(
        (FIXTURES / "github_evidence_backend.json").read_text(encoding="utf-8")
    )

    evidence = combine_evidence(collect_resume_evidence(resume), collect_github_evidence(report))

    fastapi_sources = {
        item.evidence_source for item in evidence if item.normalized_name.casefold() == "fastapi"
    }
    assert {"resume", "github"}.issubset(fastapi_sources)


def test_collect_text_evidence_uses_safe_manual_source() -> None:
    evidence = collect_text_evidence(["COREN ativo informado pelo usuario"], source="profile")

    assert evidence[0].normalized_name == "COREN"
    assert evidence[0].evidence_source == "profile"
