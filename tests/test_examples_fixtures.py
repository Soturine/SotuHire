import json
from pathlib import Path

from modules.parsers.job_description_parser import parse_job_description
from modules.parsers.resume_parser import parse_resume_text


def test_all_fictitious_resume_and_job_examples_load():
    resumes = sorted(Path("examples/resumes").glob("*.txt"))
    jobs = sorted(Path("examples/jobs").glob("*.txt"))

    assert len(resumes) >= 5
    assert len(jobs) >= 5
    assert all(parse_resume_text(path.read_text(encoding="utf-8")).name for path in resumes)
    assert all(parse_job_description(path.read_text(encoding="utf-8")).title for path in jobs)


def test_all_expected_outputs_are_valid_json():
    expected = sorted(Path("examples/expected").glob("*.json"))

    assert len(expected) >= 3
    assert all(json.loads(path.read_text(encoding="utf-8"))["fixture"] for path in expected)


def test_v1_multi_domain_demo_markdown_examples_are_fictitious():
    demo_files = sorted(Path("examples").glob("demo_*.md"))
    output_files = sorted(Path("examples/outputs").glob("match_*.md"))

    assert len(demo_files) >= 12
    assert len(output_files) >= 6
    assert all("fict" in path.read_text(encoding="utf-8").casefold() for path in demo_files)
    assert all("fict" in path.read_text(encoding="utf-8").casefold() for path in output_files)
