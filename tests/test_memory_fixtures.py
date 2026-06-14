import json
from pathlib import Path

from modules.memory import CareerMemoryItem
from modules.profile import CareerProfile

FIXTURES = Path("tests/fixtures/memory")
EXAMPLES = Path("examples/memory")


def _load_jsonl(path: Path) -> list[CareerMemoryItem]:
    return [
        CareerMemoryItem.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_memory_fixtures_are_valid_and_fictitious():
    items = _load_jsonl(FIXTURES / "career_memory_items.jsonl")
    feedback = _load_jsonl(FIXTURES / "feedback_events.jsonl")
    profile = CareerProfile.model_validate_json(
        (FIXTURES / "career_profile.json").read_text(encoding="utf-8")
    )
    expected = json.loads(
        (FIXTURES / "analysis_with_memory_expected.json").read_text(encoding="utf-8")
    )

    assert len(items) == 3
    assert {item.kind for item in feedback} == {"feedback", "tracker_event"}
    assert "Python" in profile.technical_skills
    assert expected["memory_used"] is True


def test_memory_examples_are_valid():
    items = _load_jsonl(EXAMPLES / "sample_career_memory.jsonl")
    profile = CareerProfile.model_validate_json(
        (EXAMPLES / "sample_career_profile.json").read_text(encoding="utf-8")
    )

    assert items
    assert profile.target_roles == ["Analista de Dados Junior"]
    assert (EXAMPLES / "sample_memory_summary.md").read_text(encoding="utf-8").startswith("# ")
