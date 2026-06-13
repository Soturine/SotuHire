from pathlib import Path

from modules.scraping.connectors.manual_url import ManualUrlConnector
from modules.scraping.schemas import FetchResult, ScrapingSource


class FixtureClient:
    def __init__(self, path: str):
        self.path = path

    def fetch(self, url: str, *, delay_seconds: float = 2.0) -> FetchResult:
        return FetchResult(
            url=url, status_code=200, text=Path(self.path).read_text(encoding="utf-8")
        )


def test_manual_url_detail_becomes_opportunity():
    connector = ManualUrlConnector(
        FixtureClient("tests/fixtures/html/public_job_detail_basic.html")
    )
    result = connector.collect(
        ScrapingSource(name="fixture", type="manual_url", url="https://example.com/jobs/1")
    )

    assert result.scraping_performed
    assert result.opportunities[0].title == "Desenvolvedor Python Junior"
    assert "Python" in result.opportunities[0].requirements
