from modules.memory import CareerMemory, EvidenceFeedback, MemoryStore
from modules.memory.memory_scoring import score_memory_item
from modules.memory.schemas import CareerMemoryItem


def test_useful_evidence_gains_boost_and_not_useful_loses_priority(tmp_path):
    store = MemoryStore(tmp_path / "memory.jsonl")
    memory = CareerMemory(store)
    useful = store.add_memory_item(
        CareerMemoryItem(
            kind="project",
            title="Projeto útil",
            content="Python FastAPI",
            source="resume",
        )
    )
    not_useful = store.add_memory_item(
        CareerMemoryItem(
            kind="project",
            title="Projeto não útil",
            content="Python FastAPI",
            source="resume",
        )
    )
    memory.remember_evidence_feedback(EvidenceFeedback(memory_id=useful.id, useful=True))
    memory.remember_evidence_feedback(EvidenceFeedback(memory_id=not_useful.id, useful=False))
    items = store.list_memory_items()

    useful_score = score_memory_item("Python FastAPI", useful, all_items=items)
    not_useful_score = score_memory_item("Python FastAPI", not_useful, all_items=items)

    assert useful_score.final_score > not_useful_score.final_score
    assert useful_score.components["feedback"] > 0
    assert not_useful_score.components["feedback"] < 0
