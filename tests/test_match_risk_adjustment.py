from modules.matching.requirement_matcher import match_requirement, normalize_requirement
from modules.matching.risk_adjustment import (
    build_critical_gaps,
    calculate_risk_penalty,
    risk_flags,
)


def test_missing_required_license_builds_critical_gap_and_flag() -> None:
    match = match_requirement(
        normalize_requirement("CRP obrigatorio", importance="required"),
        [],
    )

    gaps = build_critical_gaps([match])
    flags = risk_flags([match])

    assert gaps[0].severity == "knockout"
    assert "CRP" in gaps[0].reason
    assert flags == ["missing_required_license:CRP"]
    assert calculate_risk_penalty([match]) >= 35


def test_preferred_missing_requirement_does_not_build_critical_gap() -> None:
    match = match_requirement(
        normalize_requirement("Revit desejavel", importance="preferred"),
        [],
    )

    assert match.gap_severity == "medium"
    assert build_critical_gaps([match]) == []


def test_missing_required_education_builds_specific_risk_flag() -> None:
    match = match_requirement(
        normalize_requirement(
            "Graduacao em Enfermagem",
            category="education",
            importance="required",
            criticality="high",
        ),
        [],
    )

    assert risk_flags([match]) == ["missing_required_education:graduacao_em_enfermagem"]
