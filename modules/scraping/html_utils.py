"""Dependency-free HTML extraction helpers."""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin


class PublicPageParser(HTMLParser):
    """Extract visible text, title, and links from simple public HTML."""

    def __init__(self, base_url: str = "") -> None:
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self._in_title = False
        self._hidden_depth = 0
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._current_href = ""
        self._current_link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"script", "style", "noscript"}:
            self._hidden_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "a" and attributes.get("href"):
            self._current_href = urljoin(self.base_url, attributes["href"] or "")
            self._current_link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._hidden_depth:
            self._hidden_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag == "a" and self._current_href:
            label = " ".join(self._current_link_text).strip()
            self.links.append((self._current_href, label))
            self._current_href = ""
            self._current_link_text = []

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if not clean or self._hidden_depth:
            return
        if self._in_title:
            self.title = f"{self.title} {clean}".strip()
        if self._current_href:
            self._current_link_text.append(clean)
        self.text_parts.append(clean)

    @property
    def text(self) -> str:
        return "\n".join(dict.fromkeys(self.text_parts))


def parse_public_html(html: str, base_url: str = "") -> PublicPageParser:
    """Parse a public HTML page into a small extraction object."""
    parser = PublicPageParser(base_url)
    parser.feed(html)
    return parser


def probable_job_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """Return unique links whose URL or label resembles a vacancy."""
    parser = parse_public_html(html, base_url)
    markers = ("job", "jobs", "vaga", "vagas", "career", "carreira", "position", "oportunidade")
    matches = [
        (url, label)
        for url, label in parser.links
        if any(marker in f"{url} {label}".lower() for marker in markers)
    ]
    return list(dict.fromkeys(matches))
