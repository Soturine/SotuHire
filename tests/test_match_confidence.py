from modules.matching.confidence import calculate_confidence_score
from modules.matching.models import CandidateEvidence
from modules.matching.requirement_matcher import match_requirement, normalize_requirement


def test_confidence_increases_with_explicit_evidence() -> None:
    requirement = normalize_requirement(
        "Python",
        category="hard_skill",
        importance="required",
        criticality="high",
    )
    evidence = CandidateEvidence(
        skill="Python",
        normalized_name="Python",
        category="hard_skill",
        evidence_source="resume",
        evidence_text="Python em APIs backend.",
        strength="strong",
        confidence=0.9,
    )
    matched = match_requirement(requirement, [evidence])
    missing = match_requirement(requirement, [])

    high_confidence = calculate_confidence_score(
        [matched],
        [evidence],
        resume_confidence=0.9,
        job_confidence=0.9,
    )
    low_confidence = calculate_confidence_score(
        [missing],
        [],
        resume_confidence=0.25,
        job_confidence=0.25,
    )

    assert high_confidence > low_confidence


def test_confidence_reduces_with_poor_resume_and_vague_job() -> None:
    requirement = normalize_requirement("Experiencia relevante", importance="unclear")
    match = match_requirement(requirement, [])

    confidence = calculate_confidence_score(
        [match],
        [],
        resume_confidence=0.2,
        job_confidence=0.25,
    )

    assert confidence <= 0.35


def test_confidence_for_empty_match_set_is_low() -> None:
    assert calculate_confidence_score([], []) == 0.25
