from modules.matching.models import CandidateEvidence, RequirementMatch
from modules.matching.requirement_matcher import match_requirement, normalize_requirement
from modules.matching.score_calculator import calculate_match_scores


def _matched_requirement(
    name: str,
    *,
    source: str = "resume",
    strength: str = "strong",
) -> tuple[RequirementMatch, CandidateEvidence]:
    requirement = normalize_requirement(
        name,
        category="hard_skill",
        importance="required",
        criticality="high",
    )
    evidence = CandidateEvidence(
        skill=name,
        normalized_name=requirement.normalized_name,
        category=requirement.category,
        evidence_source=source,  # type: ignore[arg-type]
        evidence_text=f"Evidencia de {name}",
        evidence_file="modules/api.py" if source == "github" else "",
        strength=strength,  # type: ignore[arg-type]
        confidence=0.88,
    )
    return match_requirement(requirement, [evidence]), evidence


def test_required_requirement_missing_reduces_score_more_than_preferred_missing() -> None:
    required_missing = match_requirement(
        normalize_requirement(
            "Python", category="hard_skill", importance="required", criticality="high"
        ),
        [],
    )
    preferred_missing = match_requirement(
        normalize_requirement("FastAPI", category="hard_skill", importance="preferred"),
        [],
    )

    required_score = calculate_match_scores(
        matches=[required_missing],
        evidence=[],
        transferable_skills=[],
    )
    preferred_score = calculate_match_scores(
        matches=[preferred_missing],
        evidence=[],
        transferable_skills=[],
    )

    assert required_score.overall_score < preferred_score.overall_score
    assert required_score.risk_penalty > preferred_score.risk_penalty


def test_github_evidence_increases_portfolio_signal_and_overall_score() -> None:
    resume_match, resume_evidence = _matched_requirement("FastAPI", source="resume")
    github_match, github_evidence = _matched_requirement("FastAPI", source="github")

    resume_score = calculate_match_scores(
        matches=[resume_match],
        evidence=[resume_evidence],
        transferable_skills=[],
    )
    github_score = calculate_match_scores(
        matches=[github_match],
        evidence=[github_evidence],
        transferable_skills=[],
    )

    assert resume_score.portfolio_github_evidence_score == 0
    assert github_score.portfolio_github_evidence_score > 0
    assert github_score.overall_score > resume_score.overall_score


def test_evidence_score_stays_low_without_real_evidence() -> None:
    missing = match_requirement(
        normalize_requirement(
            "PostgreSQL", category="software", importance="required", criticality="high"
        ),
        [],
    )

    score = calculate_match_scores(matches=[missing], evidence=[], transferable_skills=[])

    assert score.evidence_score == 10


def test_seniority_mismatch_reduces_score() -> None:
    match, evidence = _matched_requirement("Python")

    aligned = calculate_match_scores(
        matches=[match],
        evidence=[evidence],
        transferable_skills=[],
        seniority_fit_score=90,
    )
    mismatched = calculate_match_scores(
        matches=[match],
        evidence=[evidence],
        transferable_skills=[],
        seniority_fit_score=35,
    )

    assert mismatched.overall_score < aligned.overall_score


def test_location_or_work_model_preference_mismatch_reduces_score() -> None:
    match, evidence = _matched_requirement("Python")

    compatible = calculate_match_scores(
        matches=[match],
        evidence=[evidence],
        transferable_skills=[],
        preferences_fit_score=90,
    )
    incompatible = calculate_match_scores(
        matches=[match],
        evidence=[evidence],
        transferable_skills=[],
        preferences_fit_score=20,
    )

    assert incompatible.opportunity_fit_score < compatible.opportunity_fit_score
    assert incompatible.overall_score < compatible.overall_score


def test_missing_required_professional_license_caps_score() -> None:
    missing_license = match_requirement(
        normalize_requirement("CREA obrigatorio", importance="required"),
        [],
    )

    score = calculate_match_scores(
        matches=[missing_license],
        evidence=[],
        transferable_skills=[],
    )

    assert score.overall_score <= 40
    assert score.risk_score >= 35
