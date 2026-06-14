from datetime import UTC, datetime, timedelta
from pathlib import Path

from modules.memory import CareerMemoryItem, CareerMemoryQuery, MemoryRetriever, MemoryStore


def test_memory_search_uses_keywords_and_tags(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.jsonl")
    store.add_memory_item(
        CareerMemoryItem(
            kind="project",
            title="Projeto de integração",
            content="Aplicação web",
            source="resume",
            tags=["FastAPI", "Python"],
        )
    )
    store.add_memory_item(
        CareerMemoryItem(
            kind="education",
            title="Curso",
            content="Curso de gestão",
            source="resume",
        )
    )

    results = MemoryRetriever(store).retrieve("vaga Python FastAPI")

    assert results
    assert results[0].title == "Projeto de integração"


def test_memory_search_boosts_recency(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.jsonl")
    old = datetime.now(UTC) - timedelta(days=365)
    for title, updated in [("Antigo", old), ("Recente", datetime.now(UTC))]:
        store.add_memory_item(
            CareerMemoryItem(
                kind="project",
                title=title,
                content="Projeto Python",
                source="resume",
                created_at=updated,
                updated_at=updated,
            )
        )

    results = store.search_memory_items(CareerMemoryQuery(query="Python", top_k=2))

    assert [item.title for item, _ in results] == ["Recente", "Antigo"]
