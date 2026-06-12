"""Recommendation helper for job analysis."""

from __future__ import annotations

from typing import Literal

Recommendation = Literal["apply", "apply_with_adjustments", "save_for_later", "ignore"]


def choose_recommendation(match_score: int, opportunity_fit_score: int, risk_score: int) -> Recommendation:
    """Choose a simple recommendation from deterministic scores."""
    if risk_score >= 80:
        return "ignore"
    if match_score >= 75 and opportunity_fit_score >= 75:
        return "apply"
    if match_score >= 65 and opportunity_fit_score >= 55:
        return "apply_with_adjustments"
    if match_score >= 50 or opportunity_fit_score >= 50:
        return "save_for_later"
    return "ignore"
