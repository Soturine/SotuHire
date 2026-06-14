from pathlib import Path

from modules.memory import CareerMemoryItem, MemoryStore


def test_add_list_update_delete_and_clear_memory(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.jsonl")
    item = store.add_memory_item(
        CareerMemoryItem(
            kind="project",
            title="Projeto API",
            content="API Python FastAPI",
            source="resume",
        )
    )

    assert store.get_memory_item(item.id) == item
    assert store.list_memory_items()[0].title == "Projeto API"

    updated = store.update_memory_item(item.id, title="Projeto API atualizado")
    assert updated.title == "Projeto API atualizado"
    assert store.delete_memory_item(item.id)
    assert not store.list_memory_items()

    store.add_memory_item(item)
    store.clear()
    assert not store.list_memory_items()
