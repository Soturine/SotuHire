from modules.github_analyzer.evidence_index import EvidenceItem
from modules.github_analyzer.repository_models import (
    RepositoryDetectedSignals,
    SelectedRepositoryFile,
)
from modules.github_analyzer.schemas import DimensionScores
from modules.github_analyzer.scoring import calculate_scores


def test_scoring_applies_security_cap_for_exposed_secret() -> None:
    scores = calculate_scores(
        dimensions=DimensionScores(
            tests=8,
            security=9,
            architecture=8,
            code_quality=8,
            documentation=8,
            consistency=8,
            maintainability=8,
            portfolio_value=8,
            resume_evidence=8,
            recruiter_readiness=8,
            job_alignment=7,
        ),
        signals=RepositoryDetectedSignals(has_tests=True, has_package_manifest=True),
        evidence_index=[
            EvidenceItem(
                claim="Possible exposed secret detected in sampled content.",
                source_file=".env",
                evidence_type="code_content",
                confidence=0.9,
            )
        ],
        selected_files=[],
    )

    assert scores.security_score <= 20
    assert scores.security_risk_level == "critical"
    assert scores.applied_caps


def test_scoring_caps_tests_for_non_trivial_repo_without_tests() -> None:
    scores = calculate_scores(
        dimensions=DimensionScores(tests=8, security=7, architecture=7, code_quality=7),
        signals=RepositoryDetectedSignals(has_tests=False, has_package_manifest=True),
        evidence_index=[],
        selected_files=[
            SelectedRepositoryFile(path="src/app.py", reason_selected="source"),
            SelectedRepositoryFile(path="src/service.py", reason_selected="source"),
            SelectedRepositoryFile(path="src/db.py", reason_selected="source"),
        ],
    )

    assert scores.test_signal_score <= 30
