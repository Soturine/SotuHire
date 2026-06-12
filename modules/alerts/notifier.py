"""Notification helpers."""

from __future__ import annotations


def should_alert(match_score: int | None, risk_score: int | None, threshold: int = 75) -> bool:
    """Return True when a job is worth alerting."""
    if match_score is None:
        return False
    if risk_score is not None and risk_score > 60:
        return False
    return match_score >= threshold
