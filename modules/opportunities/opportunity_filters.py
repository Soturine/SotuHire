"""Filter collected opportunities without network access."""

from __future__ import annotations

from modules.scraping.schemas import ScrapedOpportunity


def filter_opportunities(
    opportunities: list[ScrapedOpportunity],
    *,
    query: str = "",
    source: str = "",
) -> list[ScrapedOpportunity]:
    """Filter local opportunities by free text and source."""
    normalized_query = query.strip().lower()
    return [
        item
        for item in opportunities
        if (not source or item.source == source)
        and (
            not normalized_query
            or normalized_query
            in " ".join(
                [
                    item.title,
                    item.company or "",
                    item.location or "",
                    item.description,
                    " ".join(item.tags),
                ]
            ).lower()
        )
    ]
