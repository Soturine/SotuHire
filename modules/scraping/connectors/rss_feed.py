"""Collect opportunities from public RSS 2.0 or Atom feeds with validators."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Protocol, cast

from modules.opportunities.adapters import candidate_to_scraped
from modules.opportunities.intelligence import OpportunityCandidate
from modules.scraping.connectors.base import PublicSourceConnector
from modules.scraping.schemas import CollectionResult, FetchResult, ScrapingSource

MAX_FEED_CHARS = 2_000_000


class _ConditionalClient(Protocol):
    def fetch_conditional(
        self,
        url: str,
        *,
        etag: str = "",
        last_modified: str = "",
        delay_seconds: float = 2.0,
    ) -> FetchResult: ...


def _child_text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in element:
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local in names and child.text:
            return child.text.strip()
    return ""


def parse_feed_items(xml_text: str) -> list[tuple[str, str, str]]:
    """Backward-compatible title, link, and description tuples."""
    return [
        (item.title, item.source_url, item.description)
        for item in parse_feed_candidates(
            xml_text,
            feed_url="fixture://feed",
            source_name="feed",
        )
    ]


def parse_feed_candidates(
    xml_text: str,
    *,
    feed_url: str,
    source_name: str,
    collected_at: datetime | None = None,
) -> list[OpportunityCandidate]:
    """Preserve GUID, dates, feed kind, and provenance for RSS and Atom entries."""
    if len(xml_text) > MAX_FEED_CHARS:
        raise ValueError("Feed excede o limite seguro de coleta.")
    root = ET.fromstring(xml_text)
    root_kind = root.tag.rsplit("}", 1)[-1].casefold()
    source_kind = "atom" if root_kind == "feed" else "rss"
    observed_at = collected_at or datetime.now(UTC)
    candidates: list[OpportunityCandidate] = []
    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1].casefold() not in {"item", "entry"}:
            continue
        title = _child_text(item, ("title",))
        description = _child_text(item, ("description", "summary", "content"))
        link = _child_text(item, ("link",))
        if not link:
            link_node = next(
                (child for child in item if child.tag.rsplit("}", 1)[-1].lower() == "link"),
                None,
            )
            link = link_node.attrib.get("href", "") if link_node is not None else ""
        if not title and not description:
            continue
        external_id = _child_text(item, ("guid", "id"))
        published = _child_text(item, ("pubdate", "published", "updated"))
        organization = _child_text(item, ("author", "source"))
        source_url = link or feed_url
        candidates.append(
            OpportunityCandidate(
                source=source_name,
                source_kind=source_kind,
                source_url=source_url,
                external_id=external_id,
                title=title or "Oportunidade sem titulo",
                organization=organization,
                description=description[:100_000],
                posted_at=_datetime(published),
                structured_data={
                    "feed_url": feed_url,
                    "feed_kind": source_kind,
                    "guid": external_id,
                },
                source_refs=list(dict.fromkeys([feed_url, source_url, external_id])),
                collected_at=observed_at,
            )
        )
    return candidates


class RssFeedConnector(PublicSourceConnector):
    """Read a bounded public RSS or Atom feed with ETag/Last-Modified support."""

    def __init__(self, client=None) -> None:  # noqa: ANN001
        super().__init__(client)
        self._validators: dict[str, tuple[str, str]] = {}

    def collect(self, source: ScrapingSource) -> CollectionResult:
        try:
            response = self._fetch(source)
            if response.not_modified:
                return CollectionResult(source=source, scraping_performed=True)
            candidates = parse_feed_candidates(
                response.text,
                feed_url=source.url,
                source_name=source.name,
                collected_at=response.collected_at,
            )[: source.max_items]
            if response.etag or response.last_modified:
                self._validators[source.url] = (response.etag, response.last_modified)
            return CollectionResult(
                source=source,
                opportunities=[candidate_to_scraped(item) for item in candidates],
                new_count=len(candidates),
                scraping_performed=True,
            )
        except Exception as exc:
            return CollectionResult(source=source, failures=[str(exc)])

    def _fetch(self, source: ScrapingSource) -> FetchResult:
        etag, last_modified = self._validators.get(source.url, ("", ""))
        conditional = getattr(self.client, "fetch_conditional", None)
        if callable(conditional):
            client = cast(_ConditionalClient, self.client)
            return client.fetch_conditional(
                source.url,
                etag=etag,
                last_modified=last_modified,
                delay_seconds=source.delay_seconds,
            )
        return self.client.fetch(source.url, delay_seconds=source.delay_seconds)


def _datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


__all__ = ["RssFeedConnector", "parse_feed_candidates", "parse_feed_items"]
