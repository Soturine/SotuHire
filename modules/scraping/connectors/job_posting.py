"""Bounded schema.org JobPosting extraction from public HTML JSON-LD."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Any

from modules.opportunities.intelligence import OpportunityCandidate, utc_now

MAX_HTML_CHARS = 2_000_000
MAX_JSON_LD_BLOCKS = 64
MAX_DESCRIPTION_CHARS = 100_000


class _JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._capturing = False
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "script" or len(self.blocks) >= MAX_JSON_LD_BLOCKS:
            return
        attributes = {key.casefold(): str(value or "") for key, value in attrs}
        if attributes.get("type", "").split(";", 1)[0].strip().casefold() == (
            "application/ld+json"
        ):
            self._capturing = True
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "script" and self._capturing:
            self.blocks.append("".join(self._chunks))
            self._capturing = False
            self._chunks = []


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.casefold() in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        elif tag.casefold() in {"br", "p", "li", "div", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag.casefold() in {"p", "li", "div", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def parse_job_postings(
    html_text: str,
    *,
    source_url: str,
    collected_at: datetime | None = None,
) -> list[OpportunityCandidate]:
    """Extract JobPosting objects from objects, arrays, @graph, and nested data."""
    if len(html_text) > MAX_HTML_CHARS:
        raise ValueError("HTML excede o limite seguro para JSON-LD.")
    parser = _JsonLdParser()
    parser.feed(html_text)
    postings: list[dict[str, Any]] = []
    for block in parser.blocks:
        if len(block) > MAX_HTML_CHARS:
            continue
        try:
            value = json.loads(block)
        except (TypeError, json.JSONDecodeError):
            continue
        postings.extend(_find_postings(value))
    observed_at = collected_at or utc_now()
    return [
        _candidate(item, source_url=source_url, collected_at=observed_at)
        for item in postings
        if str(item.get("title") or item.get("name") or "").strip()
    ]


def clean_html_text(value: str) -> str:
    """Remove markup, executable elements, control characters, and excessive whitespace."""
    parser = _TextParser()
    parser.feed(html.unescape(value[:MAX_HTML_CHARS]))
    cleaned = "".join(
        character for character in "".join(parser.parts) if character >= " " or character in "\n\t"
    )
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()[:MAX_DESCRIPTION_CHARS]


def _find_postings(value: object, *, depth: int = 0) -> list[dict[str, Any]]:
    if depth > 12:
        return []
    if isinstance(value, list):
        return [item for entry in value[:500] for item in _find_postings(entry, depth=depth + 1)]
    if not isinstance(value, dict):
        return []
    found = [value] if _is_job_posting(value.get("@type")) else []
    for key, entry in list(value.items())[:500]:
        if key in {"description", "jobBenefits", "qualifications", "responsibilities"}:
            continue
        found.extend(_find_postings(entry, depth=depth + 1))
    return found


def _is_job_posting(value: object) -> bool:
    if isinstance(value, list):
        return any(_is_job_posting(item) for item in value)
    return str(value or "").rsplit("/", 1)[-1].casefold() == "jobposting"


def _candidate(
    item: dict[str, Any],
    *,
    source_url: str,
    collected_at: datetime,
) -> OpportunityCandidate:
    organization = item.get("hiringOrganization")
    organization_name = str(organization.get("name", "")) if isinstance(organization, dict) else ""
    location = _location(item.get("jobLocation"))
    employment = item.get("employmentType")
    employment_type = (
        ", ".join(str(entry) for entry in employment)
        if isinstance(employment, list)
        else str(employment or "")
    )
    external_id = item.get("identifier")
    if isinstance(external_id, dict):
        external_id = external_id.get("value") or external_id.get("name")
    remote_type = str(item.get("jobLocationType", ""))
    canonical_url = str(item.get("url", "")).strip() or source_url
    return OpportunityCandidate(
        source="schema.org",
        source_kind="schema_org",
        source_url=source_url,
        external_id=str(external_id or ""),
        title=str(item.get("title") or item.get("name") or "").strip(),
        organization=organization_name.strip(),
        location=location,
        description=clean_html_text(str(item.get("description", ""))),
        employment_type=employment_type.strip(),
        posted_at=_datetime(item.get("datePosted")),
        valid_through=_datetime(item.get("validThrough")),
        salary=_salary(item.get("baseSalary") or item.get("estimatedSalary")),
        remote=(
            "telecommute" in remote_type.casefold()
            or "remote" in remote_type.casefold()
            or "remote" in location.casefold()
        ),
        structured_data=dict(item),
        source_refs=list(dict.fromkeys([source_url, canonical_url])),
        collected_at=collected_at,
    )


def _location(value: object) -> str:
    entries = value if isinstance(value, list) else [value]
    labels: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        address = entry.get("address")
        if not isinstance(address, dict):
            continue
        labels.append(
            ", ".join(
                str(address.get(key, "")).strip()
                for key in ("addressLocality", "addressRegion", "addressCountry")
                if str(address.get(key, "")).strip()
            )
        )
    return "; ".join(item for item in labels if item)


def _salary(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    amount = value.get("value")
    amount = amount if isinstance(amount, dict) else {"value": amount}
    return {
        key: entry
        for key, entry in {
            "currency": value.get("currency"),
            "min": amount.get("minValue"),
            "max": amount.get("maxValue"),
            "value": amount.get("value"),
            "unit": amount.get("unitText"),
        }.items()
        if entry not in {None, ""}
    }


def _datetime(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


__all__ = ["clean_html_text", "parse_job_postings"]
