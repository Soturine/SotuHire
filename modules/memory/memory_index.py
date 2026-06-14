"""Dependency-free relevance scoring for career memory."""

from __future__ import annotations

from datetime import UTC, datetime

from modules.core.text_utils import extract_keywords, normalize_text
from modules.memory.schemas import CareerMemoryItem

KIND_BOOSTS = {
    "skill": 0.18,
    "project": 0.14,
    "experience": 0.14,
    "preference": 0.12,
    "feedback": 0.1,
    "job_analysis": 0.08,
    "opportunity": 0.06,
    "tracker_event": 0.05,
    "resume": 0.04,
    "education": 0.03,
}


def relevance_score(
    query: str,
    item: CareerMemoryItem,
    *,
    now: datetime | None = None,
) -> float:
    """Score keyword overlap, tags, type, confidence, and recency."""
    query_tokens = set(extract_keywords(query, limit=100))
    if not query_tokens:
        return 0.0
    content_tokens = set(extract_keywords(f"{item.title} {item.content}", limit=300))
    tag_tokens = set(extract_keywords(" ".join(item.tags), limit=100))
    overlap = len(query_tokens & content_tokens) / len(query_tokens)
    tag_overlap = len(query_tokens & tag_tokens) / len(query_tokens)
    normalized_query = normalize_text(query)
    phrase_boost = (
        0.12 if normalized_query and normalized_query in normalize_text(item.content) else 0
    )
    reference = now or datetime.now(UTC)
    updated = item.updated_at if item.updated_at.tzinfo else item.updated_at.replace(tzinfo=UTC)
    age_days = max(0, (reference - updated).days)
    recency_boost = max(0.0, 0.12 * (1 - min(age_days, 365) / 365))
    score = (
        overlap * 0.58
        + tag_overlap * 0.22
        + KIND_BOOSTS.get(item.kind, 0)
        + phrase_boost
        + recency_boost
    ) * item.confidence
    return round(min(1.0, score), 4)


def matches_filters(item: CareerMemoryItem, filters: dict[str, str]) -> bool:
    """Return whether one item matches exact normalized query filters."""
    values = item.model_dump(mode="json")
    return all(
        normalize_text(str(values.get(key, ""))) == normalize_text(value)
        for key, value in filters.items()
    )
