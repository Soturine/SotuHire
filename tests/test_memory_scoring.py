from datetime import UTC, datetime, timedelta

from modules.memory.memory_scoring import MemoryScoringWeights, score_memory_item
from modules.memory.schemas import CareerMemoryItem


def test_memory_scoring_penalizes_generic_and_old_irrelevant_items():
    now = datetime.now(UTC)
    specific = CareerMemoryItem(
        kind="project",
        title="API FastAPI",
        content="API Python FastAPI com PostgreSQL e testes.",
        source="resume",
        tags=["Python", "FastAPI"],
        updated_at=now,
    )
    generic = CareerMemoryItem(
        kind="resume",
        title="Vaga",
        content="Python",
        source="resume",
        updated_at=now - timedelta(days=900),
    )

    specific_score = score_memory_item("Python FastAPI", specific, now=now)
    generic_score = score_memory_item("Python FastAPI", generic, now=now)

    assert specific_score.final_score > generic_score.final_score
    assert generic_score.components["generic_penalty"] < 0
    assert generic_score.components["stale_penalty"] < 0


def test_memory_scoring_weights_are_configurable():
    item = CareerMemoryItem(
        kind="project",
        title="Projeto Python",
        content="Projeto Python",
        source="resume",
    )

    default = score_memory_item("Python", item)
    no_kind_boost = score_memory_item(
        "Python",
        item,
        weights=MemoryScoringWeights(kind_boosts={}),
    )

    assert default.final_score > no_kind_boost.final_score
