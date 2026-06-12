"""Minimal in-memory store for MVP/testing before a vector DB."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MemoryDocument:
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


class MemoryStore:
    """Small keyword-based memory store used as a safe MVP placeholder."""

    def __init__(self) -> None:
        self._docs: list[MemoryDocument] = []

    def add(self, document: MemoryDocument) -> None:
        self._docs.append(document)

    def search(self, query: str, limit: int = 5) -> list[MemoryDocument]:
        terms = {term.lower() for term in query.split() if len(term) > 2}
        scored = []
        for doc in self._docs:
            content = doc.content.lower()
            score = sum(1 for term in terms if term in content)
            if score:
                scored.append((score, doc))
        return [doc for _, doc in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]
