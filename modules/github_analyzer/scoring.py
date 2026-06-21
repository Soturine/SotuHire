"""Code-calculated scoring for GitHub Analyzer 2 reports."""

from __future__ import annotations

from modules.github_analyzer.dependency_graph import DependencyGraphSummary
from modules.github_analyzer.evidence_index import EvidenceItem, has_critical_secret
from modules.github_analyzer.repository_models import (
    RepositoryAnalysisInput,
    RepositoryDetectedSignals,
    RepositoryMetadata,
    SelectedRepositoryFile,
)
from modules.github_analyzer.schemas import DimensionScores, GitHubScoreBreakdown, Grade, RiskLevel


def infer_dimension_scores(
    *,
    metadata: RepositoryMetadata,
    signals: RepositoryDetectedSignals,
    selected_files: list[SelectedRepositoryFile],
    dependency_graph: DependencyGraphSummary,
    analysis_input: RepositoryAnalysisInput | None = None,
) -> DimensionScores:
    """Infer 0..10 dimension scores from deterministic repository evidence."""
    source_files = [
        file for file in selected_files if file.reason_selected in {"source", "dependency_central"}
    ]
    stack_count = len(metadata.languages) + len(_language_hints(selected_files))
    tests = 8 if signals.has_tests else 3 if _is_non_trivial(signals, selected_files) else 5
    security = 7 + int(signals.has_security_policy) + int(signals.has_env_example)
    architecture = (
        4 + min(4, len(_top_level_dirs(selected_files))) + int(bool(dependency_graph.central_files))
    )
    code_quality = 4 + min(4, len(source_files) // 3) + int(bool(dependency_graph.import_edges))
    documentation = (
        3 + int(signals.has_readme) * 3 + int(signals.has_docs) * 2 + int(signals.has_license)
    )
    consistency = (
        5 + int(signals.has_package_manifest) + int(signals.has_ci) + int(bool(source_files))
    )
    maintainability = (
        4 + int(signals.has_ci) * 2 + int(signals.has_tests) * 2 + int(signals.has_package_manifest)
    )
    portfolio_value = 4 + min(3, stack_count) + int(signals.has_readme) + int(bool(source_files))
    resume_evidence = 3 + min(4, len(source_files)) + int(signals.has_readme)
    recruiter_readiness = (
        3 + int(signals.has_readme) * 2 + int(signals.has_license) + min(3, stack_count)
    )
    job_alignment = _job_alignment_score(analysis_input, metadata, selected_files)
    return DimensionScores(
        tests=_clamp10(tests),
        security=_clamp10(security),
        architecture=_clamp10(architecture),
        code_quality=_clamp10(code_quality),
        documentation=_clamp10(documentation),
        consistency=_clamp10(consistency),
        maintainability=_clamp10(maintainability),
        portfolio_value=_clamp10(portfolio_value),
        resume_evidence=_clamp10(resume_evidence),
        recruiter_readiness=_clamp10(recruiter_readiness),
        job_alignment=_clamp10(job_alignment),
    )


def calculate_scores(
    *,
    dimensions: DimensionScores,
    signals: RepositoryDetectedSignals,
    evidence_index: list[EvidenceItem],
    selected_files: list[SelectedRepositoryFile],
) -> GitHubScoreBreakdown:
    """Calculate final scores and calibration caps from dimensions and evidence."""
    capped = dimensions.model_copy(deep=True)
    applied_caps: list[str] = []
    if has_critical_secret(evidence_index):
        capped.security = min(capped.security, 2)
        applied_caps.append("security<=2 because a likely exposed secret was detected")
    if _is_non_trivial(signals, selected_files) and not signals.has_tests:
        capped.tests = min(capped.tests, 3)
        applied_caps.append("tests<=3 because a non-trivial repository has no test signal")

    technical = _weighted(
        [
            (capped.tests, 0.20),
            (capped.security, 0.20),
            (capped.architecture, 0.15),
            (capped.code_quality, 0.15),
            (capped.documentation, 0.10),
            (capped.consistency, 0.10),
            (capped.maintainability, 0.10),
        ]
    )
    portfolio = _weighted(
        [
            (capped.portfolio_value, 0.25),
            (capped.resume_evidence, 0.25),
            (capped.recruiter_readiness, 0.20),
            (capped.documentation, 0.15),
            (capped.job_alignment, 0.15),
        ]
    )
    resume = capped.resume_evidence * 10
    recruiter = capped.recruiter_readiness * 10
    job_alignment = capped.job_alignment * 10
    overall = round(
        (technical * 0.45) + (portfolio * 0.30) + (resume * 0.15) + (job_alignment * 0.10)
    )
    confidence = _confidence(signals, evidence_index, selected_files)
    return GitHubScoreBreakdown(
        technical_score=technical,
        portfolio_score=portfolio,
        resume_evidence_score=resume,
        recruiter_readiness_score=recruiter,
        job_alignment_score=job_alignment,
        overall_score=max(0, min(100, overall)),
        documentation_score=capped.documentation * 10,
        test_signal_score=capped.tests * 10,
        security_score=capped.security * 10,
        security_risk_level=_security_risk(capped.security),
        grade=_grade(overall),
        confidence_score=confidence,
        applied_caps=applied_caps,
    )


def _weighted(values: list[tuple[int, float]]) -> int:
    return round(sum(score * 10 * weight for score, weight in values))


def _security_risk(score: int) -> RiskLevel:
    if score <= 2:
        return "critical"
    if score <= 4:
        return "high"
    if score <= 6:
        return "medium"
    return "low"


def _grade(score: int) -> Grade:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _confidence(
    signals: RepositoryDetectedSignals,
    evidence_index: list[EvidenceItem],
    selected_files: list[SelectedRepositoryFile],
) -> float:
    fetched = sum(1 for file in selected_files if file.fetched)
    base = 0.45 + min(0.25, fetched * 0.015) + min(0.20, len(evidence_index) * 0.01)
    if signals.tree_truncated:
        base -= 0.15
    if signals.has_large_files_skipped:
        base -= 0.05
    return round(max(0.1, min(0.95, base)), 2)


def _job_alignment_score(
    analysis_input: RepositoryAnalysisInput | None,
    metadata: RepositoryMetadata,
    selected_files: list[SelectedRepositoryFile],
) -> int:
    if not analysis_input or not (analysis_input.target_role or analysis_input.target_job):
        return 6 if metadata.languages or selected_files else 4
    target_text = " ".join(
        [
            analysis_input.target_role,
            " ".join(str(value) for value in analysis_input.target_job.values()),
        ]
    ).casefold()
    stack_terms = [language.casefold() for language in metadata.languages]
    stack_terms.extend(hint.casefold() for hint in _language_hints(selected_files))
    matches = sum(1 for term in set(stack_terms) if term and term.casefold() in target_text)
    return 4 + min(5, matches)


def _language_hints(files: list[SelectedRepositoryFile]) -> set[str]:
    return {file.language_hint for file in files if file.language_hint}


def _top_level_dirs(files: list[SelectedRepositoryFile]) -> set[str]:
    return {file.path.split("/", 1)[0] for file in files if "/" in file.path}


def _is_non_trivial(
    signals: RepositoryDetectedSignals, files: list[SelectedRepositoryFile]
) -> bool:
    source_count = sum(
        1 for file in files if file.reason_selected in {"source", "dependency_central"}
    )
    return bool(signals.has_package_manifest or signals.has_ci or source_count >= 3)


def _clamp10(value: int) -> int:
    return max(0, min(10, value))
