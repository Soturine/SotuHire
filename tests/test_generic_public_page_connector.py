from pathlib import Path

from modules.scraping.connectors.generic_public_page import GenericPublicPageConnector
from modules.scraping.schemas import FetchResult, ScrapingSource


class FixtureClient:
    def fetch(self, url: str, *, delay_seconds: float = 2.0) -> FetchResult:
        return FetchResult(
            url=url,
            status_code=200,
            text=Path("tests/fixtures/html/public_job_listing_links.html").read_text(
                encoding="utf-8"
            ),
        )


def test_generic_listing_extracts_probable_job_links():
    result = GenericPublicPageConnector(FixtureClient()).collect(
        ScrapingSource(
            name="listing", type="generic_public_page", url="https://example.com/careers"
        )
    )

    assert result.scraping_performed
    assert len(result.opportunities) == 2
