"""Dependency-free relevance scoring for career memory."""

from __future__ import annotations

from datetime import datetime

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
