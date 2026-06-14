from modules.memory.evidence_ranker import rank_evidence
from modules.memory.schemas import CareerMemoryItem


def test_evidence_ranker_limits_top_evidence_by_type():
    items = [
        CareerMemoryItem(
            kind="skill",
            title=f"Skill Python {index}",
            content="Python FastAPI",
            source="resume",
        )
        for index in range(5)
    ]
    items.append(
        CareerMemoryItem(
            kind="project",
            title="Projeto Python",
            content="Python FastAPI",
            source="resume",
        )
    )

    ranked = rank_evidence("Python FastAPI", items, top_k=5, limits_by_kind={"skill": 1})

    assert sum(item.kind == "skill" for item, _ in ranked) == 1
    assert any(item.kind == "project" for item, _ in ranked)
