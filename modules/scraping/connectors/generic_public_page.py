"""Collect preliminary opportunities from a public listing page."""

from __future__ import annotations

from modules.scraping.connectors.base import PublicSourceConnector
from modules.scraping.connectors.manual_url import opportunity_from_text
from modules.scraping.html_utils import probable_job_links
from modules.scraping.schemas import CollectionResult, ScrapingSource


class GenericPublicPageConnector(PublicSourceConnector):
    """Extract probable vacancy links from simple public HTML."""

    def collect(self, source: ScrapingSource) -> CollectionResult:
        try:
            response = self.client.fetch(source.url, delay_seconds=source.delay_seconds)
            links = probable_job_links(response.text, response.url)[: source.max_items]
            opportunities = [
                opportunity_from_text(
                    label or url,
                    source=source.name,
                    source_url=url,
                    title_hint=label,
                    confidence=0.55,
                )
                for url, label in links
            ]
            return CollectionResult(
                source=source,
                opportunities=opportunities,
                new_count=len(opportunities),
                scraping_performed=True,
            )
        except Exception as exc:
            return CollectionResult(source=source, failures=[str(exc)])
