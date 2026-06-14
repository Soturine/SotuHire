"""Calibrated ranking and diversity selection for career evidence."""

from __future__ import annotations

from modules.core.text_utils import normalize_text
from modules.memory.memory_filters import is_evidence_candidate, limit_by_kind
from modules.memory.memory_scoring import MemoryScore, MemoryScoringWeights, score_memory_item
from modules.memory.schemas import CareerMemoryItem


def rank_evidence(
    query: str,
    items: list[CareerMemoryItem],
    *,
    top_k: int = 5,
    filters: dict[str, str] | None = None,
    limits_by_kind: dict[str, int] | None = None,
    weights: MemoryScoringWeights | None = None,
) -> list[tuple[CareerMemoryItem, MemoryScore]]:
    """Rank evidence, remove calibration-only items, and preserve type diversity."""
    requested_filters = filters or {}
    ranked = []
    for item in items:
        if not is_evidence_candidate(item):
            continue
        values = item.model_dump(mode="json")
        if any(
            normalize_text(value) != normalize_text(str(values.get(key, "")))
            for key, value in requested_filters.items()
        ):
            continue
        score = score_memory_item(query, item, all_items=items, weights=weights)
        if score.final_score > 0:
            ranked.append((item, score))
    ranked.sort(key=lambda pair: pair[1].final_score, reverse=True)
    return limit_by_kind(ranked, top_k=top_k, limits=limits_by_kind)
