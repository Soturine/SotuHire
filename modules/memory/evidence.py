"""Convert retrieved memory into safe analysis evidence."""

from __future__ import annotations

from modules.memory.memory_scoring import MemoryScore
from modules.memory.schemas import CareerEvidence, CareerMemoryItem


def safe_excerpt(content: str, limit: int = 240) -> str:
    """Return a compact excerpt without changing the underlying fact."""
    clean = " ".join(content.split())
    return clean if len(clean) <= limit else f"{clean[: limit - 1].rstrip()}…"


def evidence_from_item(item: CareerMemoryItem, score: float | MemoryScore) -> CareerEvidence:
    """Build a traceable evidence card from one memory item."""
    detail = score if isinstance(score, MemoryScore) else MemoryScore(final_score=score)
    return CareerEvidence(
        memory_id=item.id,
        title=item.title,
        source=item.source,
        source_ref=next((ref for ref in item.source_refs if ref), item.source_id or ""),
        kind=item.kind,
        excerpt=safe_excerpt(item.content),
        relevance_score=detail.final_score,
        confidence="high"
        if item.confidence >= 0.8
        else "medium"
        if item.confidence >= 0.5
        else "low",
        confirmed_by_user=False,
        selection_reason=". ".join(detail.reasons),
        score_breakdown=detail.components,
    )
