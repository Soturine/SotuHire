"""Match Engine 2 public API."""

from modules.matching.engine import analyze_match_v2
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
