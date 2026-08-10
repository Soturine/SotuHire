"""Read-only Lever Postings API connector."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from modules.opportunities.adapters import candidate_to_scraped
from modules.opportunities.intelligence import OpportunityCandidate
from modules.scraping.connectors.base import PublicSourceConnector
from modules.scraping.connectors.job_posting import clean_html_text
from modules.scraping.schemas import CollectionResult, ScrapingSource

_API_HOST = "api.lever.co"


class LeverConnector(PublicSourceConnector):
    """Collect public postings from Lever; application submission is deliberately absent."""

    def collect_candidates(self, source: ScrapingSource) -> list[OpportunityCandidate]:
        response = self.client.fetch(_listing_url(source.url), delay_seconds=source.delay_seconds)
        payload = json.loads(response.text)
        if not isinstance(payload, list):
            raise ValueError("A API publica Lever retornou um contrato inesperado.")
        return [
            _candidate(item, organization=source.name, collected_at=response.collected_at)
            for item in payload[: source.max_items]
            if isinstance(item, dict) and str(item.get("text", "")).strip()
        ]

    def collect(self, source: ScrapingSource) -> CollectionResult:
        try:
            candidates = self.collect_candidates(source)
            return CollectionResult(
                source=source,
                opportunities=[candidate_to_scraped(item) for item in candidates],
                new_count=len(candidates),
                scraping_performed=True,
            )
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return CollectionResult(source=source, failures=[str(exc)])


def _listing_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    host = (parsed.hostname or "").casefold()
    parts = [part for part in parsed.path.split("/") if part]
    if host == _API_HOST and len(parts) >= 3 and parts[:2] == ["v0", "postings"]:
        site = parts[2]
    elif host in {"jobs.lever.co", "jobs.eu.lever.co"} and parts:
        site = parts[0]
    else:
        raise ValueError("Informe uma URL publica de site Lever.")
    if not site.replace("-", "").replace("_", "").isalnum():
        raise ValueError("O identificador do site Lever e invalido.")
    return f"https://{_API_HOST}/v0/postings/{site}?mode=json"


def _candidate(
    item: dict[str, Any],
    *,
    organization: str,
    collected_at: datetime,
) -> OpportunityCandidate:
    categories = item.get("categories")
    categories = categories if isinstance(categories, dict) else {}
    source_url = str(item.get("hostedUrl", "")).strip()
    if not source_url or "/apply" in urlsplit(source_url).path.casefold():
        raise ValueError("A resposta Lever nao contem uma URL publica de detalhe valida.")
    description = str(item.get("descriptionPlain", "")).strip()
    if not description:
        description = clean_html_text(str(item.get("description", "")))
    lists = item.get("lists")
    if isinstance(lists, list):
        description = "\n\n".join(
            part
            for part in [
                description,
                *[
                    clean_html_text(str(entry.get("content", "")))
                    for entry in lists
                    if isinstance(entry, dict)
                ],
            ]
            if part
        )
    workplace = str(item.get("workplaceType", ""))
    return OpportunityCandidate(
        source="lever",
        source_kind="lever",
        source_url=source_url,
        external_id=str(item.get("id", "")),
        title=str(item.get("text", "")).strip(),
        organization=organization.strip(),
        location=str(categories.get("location", "")).strip(),
        description=description[:100_000],
        employment_type=str(categories.get("commitment", "")).strip(),
        posted_at=_millis_datetime(item.get("createdAt")),
        remote=workplace.casefold() == "remote",
        structured_data={
            "team": categories.get("team", ""),
            "department": categories.get("department", ""),
            "workplaceType": workplace,
        },
        source_refs=[source_url, f"lever:{item.get('id', '')}"],
        collected_at=collected_at,
    )


def _millis_datetime(value: object) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(str(value)) / 1000, tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


__all__ = ["LeverConnector"]
