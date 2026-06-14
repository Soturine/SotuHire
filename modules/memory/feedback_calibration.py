"""Deterministic ranking adjustments learned from local feedback and outcomes."""

from __future__ import annotations

from modules.memory.schemas import CareerMemoryItem

USEFUL_TAG = "evidence_useful"
NOT_USEFUL_TAG = "evidence_not_useful"
POSITIVE_OUTCOMES = {"applied", "interview", "offer"}
NEGATIVE_OUTCOMES = {"ignored", "rejected", "archived"}


def evidence_feedback_adjustment(
    item: CareerMemoryItem,
    all_items: list[CareerMemoryItem],
    *,
    useful_boost: float = 0.12,
    not_useful_penalty: float = 0.18,
) -> tuple[float, str]:
    """Return an adjustment from feedback linked to one evidence memory."""
    linked = [
        feedback
        for feedback in all_items
        if feedback.kind == "feedback" and feedback.source_id == item.id
    ]
    useful = sum(USEFUL_TAG in feedback.tags for feedback in linked)
    not_useful = sum(NOT_USEFUL_TAG in feedback.tags for feedback in linked)
    adjustment = min(0.24, useful * useful_boost) - min(0.36, not_useful * not_useful_penalty)
    if useful or not_useful:
        return adjustment, f"feedback útil: {useful}; não útil: {not_useful}"
    return 0.0, ""


def outcome_adjustment(item: CareerMemoryItem) -> tuple[float, str]:
    """Boost or penalize patterns with explicit tracker outcomes."""
    normalized_tags = {tag.casefold() for tag in item.tags}
    positive = normalized_tags & POSITIVE_OUTCOMES
    negative = normalized_tags & NEGATIVE_OUTCOMES
    if positive:
        return 0.08, f"resultado positivo: {sorted(positive)[0]}"
    if negative:
        return -0.08, f"resultado negativo: {sorted(negative)[0]}"
    return 0.0, ""
