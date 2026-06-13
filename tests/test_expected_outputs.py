import json
from pathlib import Path

from modules.parsers.resume_parser import parse_resume_text


def test_resume_examples_match_expected_stable_facts():
    for expected_path in Path("examples/expected").glob("*.json"):
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        profile = parse_resume_text(
            (Path("examples") / expected["fixture"]).read_text(encoding="utf-8")
        )

        assert profile.name == expected["name"]
        assert len(profile.experiences) == expected["experience_count"]
        assert len(profile.projects) == expected["project_count"]
        assert len(profile.education) == expected["education_count"]
        assert len(profile.courses) == expected["course_count"]
        assert set(expected["required_skills"]) <= set(profile.skills)
        assert set(expected["required_links"]) <= set(profile.links)
