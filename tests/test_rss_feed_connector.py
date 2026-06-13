from pathlib import Path

from modules.scraping.connectors.rss_feed import RssFeedConnector
from modules.scraping.schemas import FetchResult, ScrapingSource


class FixtureClient:
    def fetch(self, url: str, *, delay_seconds: float = 2.0) -> FetchResult:
        return FetchResult(
            url=url,
            status_code=200,
            text=Path("tests/fixtures/html/rss_jobs.xml").read_text(encoding="utf-8"),
        )


def test_rss_feed_becomes_opportunities():
    result = RssFeedConnector(FixtureClient()).collect(
        ScrapingSource(name="feed", type="rss", url="https://example.com/jobs.xml")
    )

    assert result.scraping_performed
    assert len(result.opportunities) == 2
