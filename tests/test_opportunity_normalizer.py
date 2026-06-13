from modules.opportunities import opportunity_to_job_posting
from modules.scraping.connectors.manual_url import opportunity_from_text


def test_opportunity_can_be_analyzed_as_job_posting():
    opportunity = opportunity_from_text(
        "Cargo: Dev Python\nEmpresa: Example\nPython SQL remoto",
        source="fixture",
        source_url="https://example.com/jobs/1",
    )

    job = opportunity_to_job_posting(opportunity)

    assert job.title == "Dev Python"
    assert job.raw_text
    assert job.modality == "remote"
