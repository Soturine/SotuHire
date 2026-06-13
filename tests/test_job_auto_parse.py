from modules.examples import load_default_job_example
from modules.parsers.job_description_parser import parse_job_description


def test_empty_job_text_does_not_break():
    parsed = parse_job_description("")

    assert parsed.raw_text == ""
    assert parsed.risk_flags == ["Descrição da vaga vazia."]


def test_default_job_example_fills_detected_data():
    parsed = parse_job_description(load_default_job_example())

    assert parsed.title
    assert parsed.company
    assert parsed.modality != "unknown"
    assert parsed.seniority
    assert parsed.required_skills
