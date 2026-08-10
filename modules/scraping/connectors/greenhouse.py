"""Read-only Greenhouse Job Board API connector."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from modules.opportunities.adapters import candidate_to_scraped
from modules.opportunities.intelligence import OpportunityCandidate
from modules.scraping.connectors.base import PublicSourceConnector
from modules.scraping.connectors.job_posting import clean_html_text
from modules.scraping.schemas import CollectionResult, ScrapingSource

_API_HOST = "boards-api.greenhouse.io"


class GreenhouseConnector(PublicSourceConnector):
    """Collect jobs from official public list/detail endpoints; never apply endpoints."""

    def collect_candidates(self, source: ScrapingSource) -> list[OpportunityCandidate]:
        response = self.client.fetch(_listing_url(source.url), delay_seconds=source.delay_seconds)
        payload = json.loads(response.text)
        jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
        organization = _organization(payload, source.name)
        return [
            _candidate(item, organization=organization, collected_at=response.collected_at)
            for item in jobs[: source.max_items]
            if isinstance(item, dict) and str(item.get("title", "")).strip()
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
    if host == _API_HOST and len(parts) >= 4 and parts[:2] == ["v1", "boards"]:
        token = parts[2]
    elif host in {"boards.greenhouse.io", "job-boards.greenhouse.io"} and parts:
        token = parts[0]
    else:
        raise ValueError("Informe uma URL publica de board Greenhouse.")
    if not token.replace("-", "").replace("_", "").isalnum():
        raise ValueError("O identificador do board Greenhouse e invalido.")
    return f"https://{_API_HOST}/v1/boards/{token}/jobs?content=true"


def _candidate(
    item: dict[str, Any],
    *,
    organization: str,
    collected_at: datetime,
) -> OpportunityCandidate:
    location = item.get("location")
    location_name = str(location.get("name", "")) if isinstance(location, dict) else ""
    external_id = str(item.get("id", ""))
    source_url = str(item.get("absolute_url", "")).strip()
    if not source_url or "/apply" in urlsplit(source_url).path.casefold():
        raise ValueError("A resposta Greenhouse nao contem uma URL publica de detalhe valida.")
    content = clean_html_text(str(item.get("content", "")))
    return OpportunityCandidate(
        source="greenhouse",
        source_kind="greenhouse",
        source_url=source_url,
        external_id=external_id,
        title=str(item.get("title", "")).strip(),
        organization=organization,
        location=location_name,
        description=content,
        employment_type=_metadata_value(item.get("metadata"), "employment type"),
        posted_at=_datetime(item.get("updated_at")),
        remote="remote" in location_name.casefold(),
        structured_data={
            "departments": item.get("departments", []),
            "offices": item.get("offices", []),
            "metadata": item.get("metadata", []),
        },
        source_refs=[source_url, f"greenhouse:{external_id}"],
        collected_at=collected_at,
    )


def _organization(payload: dict[str, Any], fallback: str) -> str:
    meta = payload.get("meta")
    if isinstance(meta, dict):
        for key in ("name", "company_name", "organization"):
            if meta.get(key):
                return str(meta[key]).strip()
    return fallback.strip()


def _metadata_value(value: object, wanted: str) -> str:
    if not isinstance(value, list):
        return ""
    for item in value:
        if not isinstance(item, dict) or str(item.get("name", "")).casefold() != wanted:
            continue
        result = item.get("value")
        return str(result).strip() if result is not None else ""
    return ""


def _datetime(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


__all__ = ["GreenhouseConnector"]
