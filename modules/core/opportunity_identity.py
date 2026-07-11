"""Stable identity helpers shared by captures, opportunities, and tracker records."""

from __future__ import annotations

import hashlib
from urllib.parse import urlsplit

from modules.core.entity_identity import normalize_entity_url
from modules.core.text_utils import normalize_text

TITLE_STOPWORDS = {
    "a",
    "da",
    "de",
    "do",
    "e",
    "em",
    "para",
    "pessoa",
    "vaga",
}
TITLE_ALIASES = {
    "jr": "junior",
    "sr": "senior",
}


def normalize_opportunity_url(url: str) -> str:
    """Remove volatile URL parts while preserving a stable job path."""
    if not url.strip():
        return ""
    return normalize_entity_url(url)


def opportunity_identity(title: str, company: str = "", source_url: str = "") -> str:
    """Return a stable identity, preferring a normalized source URL."""
    normalized_url = normalize_opportunity_url(source_url)
    if normalized_url:
        return f"url:{normalized_url}"
    return f"job:{normalize_text(title)}|{normalize_text(company)}"


def opportunity_identity_hash(title: str, company: str = "", source_url: str = "") -> str:
    """Return a compact deterministic id for a captured opportunity."""
    value = opportunity_identity(title, company, source_url)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_domain(url: str) -> str:
    """Return the source hostname without a leading www."""
    domain = urlsplit(url.strip()).netloc.casefold()
    return domain.removeprefix("www.")


def same_opportunity(
    *,
    left_title: str,
    left_company: str = "",
    left_urls: list[str] | None = None,
    right_title: str,
    right_company: str = "",
    right_url: str = "",
) -> bool:
    """Match the same vacancy across tracking URLs and different job portals."""
    normalized_right_url = normalize_opportunity_url(right_url)
    if normalized_right_url and any(
        normalize_opportunity_url(url) == normalized_right_url for url in left_urls or []
    ):
        return True

    left_company_key = normalize_text(left_company)
    right_company_key = normalize_text(right_company)
    if not left_company_key or left_company_key != right_company_key:
        return False

    left_title_key = normalize_text(left_title)
    right_title_key = normalize_text(right_title)
    if left_title_key == right_title_key:
        return True

    left_tokens = _title_tokens(left_title_key)
    right_tokens = _title_tokens(right_title_key)
    overlap = left_tokens & right_tokens
    union = left_tokens | right_tokens
    return len(overlap) >= 2 and bool(union) and len(overlap) / len(union) >= 0.72


def _title_tokens(normalized_title: str) -> set[str]:
    return {
        TITLE_ALIASES.get(token, token)
        for token in normalized_title.split()
        if len(token) > 1 and token not in TITLE_STOPWORDS
    }
