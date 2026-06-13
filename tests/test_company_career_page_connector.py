from pathlib import Path

from modules.scraping.connectors.company_career_page import CompanyCareerPageConnector
from modules.scraping.schemas import FetchResult, ScrapingSource


class FixtureClient:
    def fetch(self, url: str, *, delay_seconds: float = 2.0) -> FetchResult:
        return FetchResult(
            url=url,
            status_code=200,
            text=Path("tests/fixtures/html/company_career_page.html").read_text(encoding="utf-8"),
        )


def test_company_career_page_extracts_job_links():
    result = CompanyCareerPageConnector(FixtureClient()).collect(
        ScrapingSource(
            name="careers", type="company_career_page", url="https://example.com/careers"
        )
    )

    assert len(result.opportunities) == 2
