from modules.matching.domain_weights import DEFAULT_MATCH_WEIGHTS, weights_for_domain
from modules.matching.models import CandidateEvidence
from modules.matching.requirement_matcher import match_requirement, normalize_requirement
from modules.matching.score_calculator import calculate_match_scores


def test_domain_weights_sum_to_one() -> None:
    domains = [
        "",
        "nursing",
        "healthcare",
        "architecture",
        "cybersecurity",
        "pedagogy",
        "engineering",
        "civil_engineering",
    ]

    for domain in domains:
        assert round(weights_for_domain(domain).total(), 2) == 1.0


def test_healthcare_weights_reduce_github_importance_and_raise_credentials() -> None:
    healthcare = weights_for_domain("enfermagem")

    assert healthcare.portfolio_github_evidence == 0.0
    assert healthcare.education_credentials > DEFAULT_MATCH_WEIGHTS.education_credentials


def test_architecture_weights_value_portfolio_more_than_healthcare() -> None:
    architecture = weights_for_domain("architecture")
    healthcare = weights_for_domain("healthcare")

    assert architecture.portfolio_github_evidence > healthcare.portfolio_github_evidence
    assert architecture.evidence_strength > healthcare.evidence_strength


def test_domain_weights_change_score_contribution() -> None:
    requirement = normalize_requirement(
        "FastAPI",
        category="hard_skill",
        importance="required",
        criticality="high",
    )
    evidence = CandidateEvidence(
        skill="FastAPI",
        normalized_name="FastAPI",
        category="hard_skill",
        evidence_source="github",
        evidence_text="FastAPI em projeto publico.",
        evidence_file="modules/api.py",
        strength="strong",
        confidence=0.9,
    )
    match = match_requirement(requirement, [evidence])

    healthcare_score = calculate_match_scores(
        matches=[match],
        evidence=[evidence],
        transferable_skills=[],
        weights=weights_for_domain("healthcare"),
    )
    architecture_score = calculate_match_scores(
        matches=[match],
        evidence=[evidence],
        transferable_skills=[],
        weights=weights_for_domain("architecture"),
    )

    assert architecture_score.overall_score > healthcare_score.overall_score
