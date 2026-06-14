from pathlib import Path

from modules.memory import CareerFeedback, CareerMemory, MemoryStore


def test_feedback_becomes_searchable_memory(tmp_path: Path):
    memory = CareerMemory(MemoryStore(tmp_path / "memory.jsonl"))

    saved = memory.remember_feedback(
        CareerFeedback(
            rating="partial",
            reason="A vaga era boa, mas presencial",
            change_requested="Priorizar remoto",
            applied=False,
        )
    )

    assert saved.kind == "feedback"
    assert memory.retriever.retrieve("priorizar remoto")[0].memory_id == saved.id
