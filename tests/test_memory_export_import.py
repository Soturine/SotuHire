from pathlib import Path

from modules.memory import CareerMemory, CareerMemoryItem, MemoryStore


def test_memory_export_import_and_markdown_summary(tmp_path: Path):
    source = MemoryStore(tmp_path / "source.jsonl")
    source.add_memory_item(
        CareerMemoryItem(
            kind="skill",
            title="Skill Python",
            content="Python",
            source="resume",
            tags=["Python"],
        )
    )
    exports = CareerMemory(source).export_all(tmp_path / "exports")
    target = MemoryStore(tmp_path / "target.jsonl")

    imported = target.import_file(exports["json"])

    assert imported == 1
    assert target.list_memory_items()[0].title == "Skill Python"
    assert "Resumo da memória" in exports["markdown"].read_text(encoding="utf-8")
