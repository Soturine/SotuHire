from modules.memory import CareerMemoryItem, evidence_from_item


def test_evidence_is_traceable_and_compact():
    item = CareerMemoryItem(
        kind="experience",
        title="Experiência industrial",
        content="Processos técnicos " * 40,
        source="resume",
    )

    evidence = evidence_from_item(item, 0.82)

    assert evidence.memory_id == item.id
    assert evidence.source == "resume"
    assert evidence.relevance_score == 0.82
    assert len(evidence.excerpt) <= 240
