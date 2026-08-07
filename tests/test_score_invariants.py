from __future__ import annotations

from modules.matching.models import CandidateEvidence, RequirementMatch
from modules.matching.requirement_matcher import match_requirement, normalize_requirement
from modules.matching.score_calculator import calculate_match_scores


def test_unknown_reduces_confidence_without_changing_known_fit_or_coverage() -> None:
    known_requirement = normalize_requirement(
        "Python", importance="required", category="hard_skill", confidence=0.9
    )
    evidence = CandidateEvidence(
        skill="Python",
        normalized_name=known_requirement.normalized_name,
        category="hard_skill",
        evidence_source="resume",
        evidence_text="Python em projeto confirmado.",
        strength="strong",
        confidence=0.9,
    )
    met = match_requirement(known_requirement, [evidence])
    unknown = match_requirement(
        normalize_requirement(
            "Requisito ambíguo",
            importance="required",
            category="other",
            confidence=0.4,
        ),
        [],
    )

    known_only = calculate_match_scores(matches=[met], evidence=[evidence], transferable_skills=[])
    with_unknown = calculate_match_scores(
        matches=[met, unknown], evidence=[evidence], transferable_skills=[]
    )

    assert unknown.match_status == "unknown"
    assert with_unknown.assessed_match_score == known_only.assessed_match_score
    assert with_unknown.requirement_coverage == known_only.requirement_coverage == 1.0
    assert with_unknown.confidence_score < known_only.confidence_score
    assert with_unknown.unknown_requirement_count == 1


def test_not_applicable_is_excluded_and_all_unknown_is_nullable() -> None:
    requirement = normalize_requirement("GitHub", importance="optional", confidence=0.9)
    not_applicable = RequirementMatch(
        requirement=requirement,
        match_status="not_applicable",
        gap_severity="none",
        safe_action="Não se aplica a esta profissão.",
    )
    unknown = match_requirement(
        normalize_requirement("Licença não especificada", importance="required", confidence=0.3),
        [],
    )

    result = calculate_match_scores(
        matches=[not_applicable, unknown], evidence=[], transferable_skills=[]
    )

    assert result.assessed_match_score is None
    assert result.requirement_coverage is None
    assert result.requirement_coverage_status == "insufficient"
    assert result.applicable_requirement_count == 0
    assert result.not_applicable_requirement_count == 1
