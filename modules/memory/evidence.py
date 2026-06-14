"""Convert retrieved memory into safe analysis evidence."""

from __future__ import annotations

from modules.memory.schemas import CareerEvidence, CareerMemoryItem


def safe_excerpt(content: str, limit: int = 240) -> str:
    """Return a compact excerpt without changing the underlying fact."""
    clean = " ".join(content.split())
    return clean if len(clean) <= limit else f"{clean[: limit - 1].rstrip()}…"


def evidence_from_item(item: CareerMemoryItem, score: float) -> CareerEvidence:
    """Build a traceable evidence card from one memory item."""
    return CareerEvidence(
        memory_id=item.id,
        title=item.title,
        source=item.source,
        excerpt=safe_excerpt(item.content),
        relevance_score=score,
    )
