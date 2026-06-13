"""Collect opportunities from public RSS or Atom feeds."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from modules.scraping.connectors.base import PublicSourceConnector
from modules.scraping.connectors.manual_url import opportunity_from_text
from modules.scraping.schemas import CollectionResult, ScrapingSource


def _child_text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in element:
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local in names and child.text:
            return child.text.strip()
    return ""


def parse_feed_items(xml_text: str) -> list[tuple[str, str, str]]:
    """Return title, link, and description tuples from RSS or Atom XML."""
    root = ET.fromstring(xml_text)
    items: list[tuple[str, str, str]] = []
    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1].lower() not in {"item", "entry"}:
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
        if title or description:
            items.append((title, link, description))
    return items


class RssFeedConnector(PublicSourceConnector):
    """Read a bounded public RSS or Atom feed."""

    def collect(self, source: ScrapingSource) -> CollectionResult:
        try:
            response = self.client.fetch(source.url, delay_seconds=source.delay_seconds)
            opportunities = [
                opportunity_from_text(
                    f"{title}\n{description}",
                    source=source.name,
                    source_url=link or response.url,
                    title_hint=title,
                    confidence=0.75,
                )
                for title, link, description in parse_feed_items(response.text)[: source.max_items]
            ]
            return CollectionResult(
                source=source,
                opportunities=opportunities,
                new_count=len(opportunities),
                scraping_performed=True,
            )
        except Exception as exc:
            return CollectionResult(source=source, failures=[str(exc)])
