"""Confidence scoring for Match Engine 2."""

from __future__ import annotations

from modules.matching.models import CandidateEvidence, RequirementMatch


def calculate_confidence_score(
    matches: list[RequirementMatch],
    evidence: list[CandidateEvidence],
    *,
    resume_confidence: float = 0.6,
    job_confidence: float = 0.6,
) -> float:
    """Calculate confidence separately from score quality."""
    if not matches:
        return 0.25
    matched = [item for item in matches if item.match_status in {"matched", "partial"}]
    explicit_evidence = [item for item in evidence if item.confidence >= 0.65]
    coverage = len(matched) / len(matches)
    evidence_strength = min(1.0, len(explicit_evidence) / max(1, len(matches)))
    match_confidence = sum(item.confidence for item in matches) / len(matches)
    base = (
        coverage * 0.25
        + evidence_strength * 0.20
        + match_confidence * 0.25
        + resume_confidence * 0.15
        + job_confidence * 0.15
    )
    if not explicit_evidence:
        base -= 0.15
    return round(max(0.1, min(0.98, base)), 2)
