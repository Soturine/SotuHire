"""Portfolio scoring helpers."""

from __future__ import annotations

from modules.core.scoring import weighted_score


def calculate_portfolio_score(
    readme: int | None, tests: int | None, architecture: int | None, alignment: int | None
) -> int | None:
    """Calculate portfolio score from deterministic sub-scores."""
    return weighted_score(
        {"readme": readme, "tests": tests, "architecture": architecture, "alignment": alignment},
        {"readme": 0.30, "tests": 0.20, "architecture": 0.25, "alignment": 0.25},
    )
