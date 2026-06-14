"""Stable identity helpers shared by captures, opportunities, and tracker records."""

from __future__ import annotations

import hashlib
from urllib.parse import urlsplit, urlunsplit

from modules.core.text_utils import normalize_text


def normalize_opportunity_url(url: str) -> str:
    """Remove volatile URL parts while preserving a stable job path."""
    if not url.strip():
        return ""
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), path, "", ""))


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
