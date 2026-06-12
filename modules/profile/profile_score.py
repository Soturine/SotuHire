"""Profile score helpers for LinkedIn, Lattes and portfolio signals."""

from __future__ import annotations

from modules.core.scoring import weighted_score


def calculate_readiness_score(
    ats_score: int | None,
    match_score: int | None,
    linkedin_score: int | None = None,
    portfolio_score: int | None = None,
) -> int | None:
    """Combine core scores into a readiness score."""
    return weighted_score(
        {
            "ats": ats_score,
            "match": match_score,
            "linkedin": linkedin_score,
            "portfolio": portfolio_score,
        },
        {
            "ats": 0.25,
            "match": 0.45,
            "linkedin": 0.15,
            "portfolio": 0.15,
        },
    )
