"""Collect one public vacancy detail URL."""

from __future__ import annotations

import hashlib
from urllib.parse import urlparse

from modules.core.collection_method import CollectionMethod
from modules.parsers.job_description_parser import parse_job_description
from modules.scraping.connectors.base import PublicSourceConnector
from modules.scraping.html_utils import parse_public_html
from modules.scraping.schemas import CollectionResult, ScrapedOpportunity, ScrapingSource


def opportunity_from_text(
    text: str,
    *,
    source: str,
    source_url: str,
    title_hint: str = "",
    confidence: float = 0.8,
    collection_method: CollectionMethod = "manual_url",
) -> ScrapedOpportunity:
    """Normalize extracted public text into a scraped opportunity."""
    parsed = parse_job_description(text)
    title = parsed.title or title_hint or urlparse(source_url).path.rstrip("/").split("/")[-1]
    content_hash = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
    salary_text = ""
    if parsed.salary_min:
        salary_text = f"R$ {parsed.salary_min}"
        if parsed.salary_max and parsed.salary_max != parsed.salary_min:
            salary_text += f" - R$ {parsed.salary_max}"
    return ScrapedOpportunity(
        source=source,
        source_url=source_url,
        title=title or "Vaga pública",
        company=parsed.company or None,
        location=parsed.location or None,
        modality=None if parsed.modality == "unknown" else parsed.modality,
        seniority=parsed.seniority or None,
        contract_type=parsed.contract or None,
        salary_text=salary_text or None,
        description=text.strip(),
        requirements=parsed.required_skills,
        benefits=parsed.benefits,
        tags=parsed.ats_keywords[:12],
        content_hash=content_hash,
        confidence=confidence,
        collection_method=collection_method,
    )


class ManualUrlConnector(PublicSourceConnector):
    """Download and normalize one explicit public URL."""

    def collect(self, source: ScrapingSource) -> CollectionResult:
        try:
            response = self.client.fetch(source.url, delay_seconds=source.delay_seconds)
            page = parse_public_html(response.text, response.url)
            opportunity = opportunity_from_text(
                page.text,
                source=source.name,
                source_url=response.url,
                title_hint=page.title,
            )
            return CollectionResult(
                source=source,
                opportunities=[opportunity],
                new_count=1,
                scraping_performed=True,
            )
        except Exception as exc:
            return CollectionResult(source=source, failures=[str(exc)])
