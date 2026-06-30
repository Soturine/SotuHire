"""Unified career context for local-first SotuHire workflows."""

from .engine import CareerContextEngine
from .formatters import (
    context_brief,
    context_to_memory_evidence,
    format_context_for_prompt,
    profile_context_from_career_context,
    profile_evidence_candidates_from_github_report,
)
from .models import CareerContext, CareerContextEvidence, CareerContextPurpose

__all__ = [
    "CareerContext",
    "CareerContextEngine",
    "CareerContextEvidence",
    "CareerContextPurpose",
    "context_brief",
    "context_to_memory_evidence",
    "format_context_for_prompt",
    "profile_context_from_career_context",
    "profile_evidence_candidates_from_github_report",
]
