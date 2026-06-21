"""Match Engine 2 public API."""

from typing import Any

from modules.matching.models import (
    OTHER_PROFESSIONAL_REGISTRATION_OPTION,
    CandidateEvidence,
    CriticalGap,
    MatchExplanation,
    MatchRequirement,
    MatchResultV2,
    MatchScoreBreakdown,
    ProfessionalRegistrationInput,
    RequirementMatch,
    TransferableSkillMatch,
)


def analyze_match_v2(*args: Any, **kwargs: Any) -> MatchResultV2:
    """Run Match Engine 2 while keeping package imports lightweight."""
    from modules.matching.engine import analyze_match_v2 as _analyze_match_v2

    return _analyze_match_v2(*args, **kwargs)


__all__ = [
    "analyze_match_v2",
    "CandidateEvidence",
    "CriticalGap",
    "MatchExplanation",
    "MatchRequirement",
    "MatchResultV2",
    "MatchScoreBreakdown",
    "OTHER_PROFESSIONAL_REGISTRATION_OPTION",
    "ProfessionalRegistrationInput",
    "RequirementMatch",
    "TransferableSkillMatch",
]
