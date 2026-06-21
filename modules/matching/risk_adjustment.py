"""Risk and critical gap adjustment for Match Engine 2."""

from __future__ import annotations

from modules.matching.models import CriticalGap, RequirementMatch


def build_critical_gaps(matches: list[RequirementMatch]) -> list[CriticalGap]:
    """Return high/knockout gaps with safe actions."""
    gaps: list[CriticalGap] = []
    for match in matches:
        if match.gap_severity not in {"high", "knockout"}:
            continue
        gaps.append(
            CriticalGap(
                requirement=match.requirement,
                severity=match.gap_severity,
                reason=_gap_reason(match),
                safe_action=match.safe_action,
            )
        )
    return gaps


def calculate_risk_penalty(matches: list[RequirementMatch]) -> int:
    """Calculate penalty applied to the overall score."""
    penalty = 0
    for match in matches:
        if match.match_status != "missing":
            continue
        if match.gap_severity == "knockout":
            penalty += 35
        elif match.gap_severity == "high":
            penalty += 18
        elif match.gap_severity == "medium":
            penalty += 8
        elif match.gap_severity == "low":
            penalty += 3
    return min(80, penalty)


def risk_flags(matches: list[RequirementMatch]) -> list[str]:
    """Return human-readable risk flags."""
    flags: list[str] = []
    for gap in build_critical_gaps(matches):
        if gap.requirement.category in {"professional_license", "professional_registration"}:
            flags.append(f"missing_required_license:{gap.requirement.normalized_name}")
        elif gap.requirement.category == "education":
            flags.append(f"missing_required_education:{gap.requirement.normalized_name}")
        elif gap.requirement.category == "experience":
            flags.append(f"missing_required_experience:{gap.requirement.normalized_name}")
        else:
            flags.append(f"missing_required_requirement:{gap.requirement.normalized_name}")
    return flags


def _gap_reason(match: RequirementMatch) -> str:
    requirement = match.requirement
    if requirement.category in {"professional_license", "professional_registration"}:
        return (
            f"A vaga exige {requirement.normalized_name} e não há evidência desse registro "
            "nas fontes analisadas."
        )
    return f"Requisito obrigatório ausente ou sem evidência suficiente: {requirement.requirement_text}."
