"""Deterministic scoring helpers.

The AI can explain scores, but basic normalization and weighted averages should be
kept deterministic and unit-tested.
"""

from __future__ import annotations


def clamp_score(value: int | float | None) -> int | None:
    """Clamp a numeric score to the 0-100 range."""
    if value is None:
        return None
    return max(0, min(100, int(round(value))))


def weighted_score(values: dict[str, int | None], weights: dict[str, float]) -> int | None:
    """Return a weighted score ignoring missing values."""
    total = 0.0
    weight_sum = 0.0
    for key, score in values.items():
        if score is None:
            continue
        weight = weights.get(key, 0.0)
        total += clamp_score(score) * weight
        weight_sum += weight
    if weight_sum == 0:
        return None
    return clamp_score(total / weight_sum)
