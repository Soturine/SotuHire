"""Dependency-free relevance scoring for career memory."""

from __future__ import annotations

from datetime import datetime

from modules.core.text_utils import normalize_text
from modules.memory.memory_scoring import score_memory_item
from modules.memory.schemas import CareerMemoryItem


def relevance_score(
    query: str,
    item: CareerMemoryItem,
    *,
    now: datetime | None = None,
) -> float:
    """Score keyword overlap, tags, type, confidence, and recency."""
    return score_memory_item(query, item, now=now).final_score


def matches_filters(item: CareerMemoryItem, filters: dict[str, str]) -> bool:
    """Return whether one item matches exact normalized query filters."""
    values = item.model_dump(mode="json")
    return all(
        normalize_text(str(values.get(key, ""))) == normalize_text(value)
        for key, value in filters.items()
    )
