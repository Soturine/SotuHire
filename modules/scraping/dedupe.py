"""Opportunity identity and deduplication helpers."""

from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from modules.scraping.schemas import ScrapedOpportunity

TRACKING_PARAMS = {"fbclid", "gclid", "ref", "source", "utm_campaign", "utm_medium", "utm_source"}


def normalize_url(url: str) -> str:
    """Remove fragments and common tracking parameters from a source URL."""
    parts = urlsplit(url.strip())
    query = urlencode(
        sorted((key, value) for key, value in parse_qsl(parts.query) if key not in TRACKING_PARAMS)
    )
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, "")
    )


def opportunity_identity(opportunity: ScrapedOpportunity) -> tuple[str, str, str]:
    """Return URL, semantic, and content identities."""
    semantic = "\0".join(
        [
            opportunity.title.strip().lower(),
            (opportunity.company or "").strip().lower(),
            opportunity.description.strip().lower(),
        ]
    )
    return (
        normalize_url(opportunity.source_url),
        hashlib.sha256(semantic.encode("utf-8")).hexdigest(),
        opportunity.content_hash,
    )


def deduplicate_opportunities(
    opportunities: list[ScrapedOpportunity],
) -> tuple[list[ScrapedOpportunity], int]:
    """Remove duplicates while preserving source order."""
    unique: list[ScrapedOpportunity] = []
    seen: set[str] = set()
    duplicate_count = 0
    for opportunity in opportunities:
        identities = set(opportunity_identity(opportunity))
        if identities & seen:
            duplicate_count += 1
            continue
        unique.append(opportunity)
        seen.update(identities)
    return unique, duplicate_count
