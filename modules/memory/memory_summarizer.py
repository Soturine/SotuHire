"""Safe summaries for local or explicitly shared memory context."""

from __future__ import annotations

from collections import Counter

from modules.memory.schemas import CareerEvidence, CareerMemoryItem


def summarize_evidence(evidence: list[CareerEvidence], limit: int = 5) -> str:
    """Build a compact evidence-only context without the full memory store."""
    return "\n".join(f"- {item.title} ({item.source}): {item.excerpt}" for item in evidence[:limit])


def memory_markdown_summary(items: list[CareerMemoryItem]) -> str:
    """Build a portable Markdown overview of local memory."""
    kinds = Counter(item.kind for item in items)
    tags = Counter(tag for item in items for tag in item.tags)
    lines = [
        "# Resumo da memória de carreira",
        "",
        f"Total de itens: {len(items)}",
        "",
        "## Tipos",
        *[f"- {kind}: {count}" for kind, count in kinds.most_common()],
        "",
        "## Tags recorrentes",
        *[f"- {tag}: {count}" for tag, count in tags.most_common(15)],
        "",
        "## Itens recentes",
        *[f"- **{item.title}** ({item.kind}) — {item.source}" for item in items[:10]],
    ]
    return "\n".join(lines)
