"""Retrieve safe evidence from local career memory."""

from __future__ import annotations

from modules.memory.evidence import evidence_from_item
from modules.memory.memory_store import MemoryStore
from modules.memory.schemas import CareerEvidence, CareerMemoryQuery


class MemoryRetriever:
    """Dependency-free local RAG retriever."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def retrieve(self, query: CareerMemoryQuery | str, top_k: int = 5) -> list[CareerEvidence]:
        """Return traceable evidence ordered by local relevance."""
        request = (
            query
            if isinstance(query, CareerMemoryQuery)
            else CareerMemoryQuery(query=query, top_k=top_k)
        )
        return [
            evidence_from_item(item, score)
            for item, score in self.store.search_memory_items(request)
        ]
