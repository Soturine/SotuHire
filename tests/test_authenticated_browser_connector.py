from modules.scraping.connectors.authenticated_browser import (
    AuthenticatedBrowserConnector,
    BrowserCapture,
    selectors_for_source,
)
from modules.scraping.schemas import ScrapingSource


class FixtureAuthenticatedCrawler:
    def crawl(self, source: ScrapingSource) -> list[BrowserCapture]:
        assert source.authorized_use
        return [
            BrowserCapture(
                url="https://www.linkedin.com/jobs/view/123",
                title="Python Developer",
                text="Cargo: Python Developer\nEmpresa: Example\nPython SQL remoto",
            ),
            BrowserCapture(
                url="https://www.linkedin.com/jobs/view/123",
                title="Python Developer",
                text="Cargo: Python Developer\nEmpresa: Example\nPython SQL remoto",
            ),
        ]


def authenticated_source(**changes: object) -> ScrapingSource:
    payload = {
        "name": "LinkedIn autorizado",
        "type": "authenticated_browser",
        "url": "https://www.linkedin.com/jobs/search/?keywords=python",
        "collection_mode": "AUTHENTICATED_BROWSER",
        "authorized_use": True,
        "authorization_reference": "Teste autorizado",
    }
    payload.update(changes)
    return ScrapingSource.model_validate(payload)


def test_linkedin_authenticated_presets_cover_jobs_and_posts():
    jobs = selectors_for_source(authenticated_source())
    posts = selectors_for_source(authenticated_source(url="https://www.linkedin.com/feed/"))

    assert "/jobs/view/" in jobs["link"]
    assert "next" in jobs
    assert "item" in posts
    assert "/feed/update/" in posts["item_link"]


def test_authenticated_connector_requires_explicit_authorization():
    source = authenticated_source(authorized_use=False)

    result = AuthenticatedBrowserConnector(crawler=FixtureAuthenticatedCrawler()).collect(source)

    assert result.authenticated_browser
    assert not result.scraping_performed
    assert result.failures


def test_authenticated_connector_normalizes_and_deduplicates_captures():
    result = AuthenticatedBrowserConnector(crawler=FixtureAuthenticatedCrawler()).collect(
        authenticated_source()
    )

    assert result.authenticated_browser
    assert result.scraping_performed
    assert result.new_count == 1
    assert result.duplicate_count == 1
    assert result.opportunities[0].title == "Python Developer"
