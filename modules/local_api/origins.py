"""Exact local origins trusted by the browser Companion."""

from __future__ import annotations

import os
import re

DEFAULT_EXTENSION_ID = "joodapjganjanoaaogapmjhcellljnfg"
_EXTENSION_ID = re.compile(r"^[a-p]{32}$")
_WEB_ORIGINS = frozenset(
    {
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    }
)


def extension_origins() -> frozenset[str]:
    configured = {
        value.strip()
        for value in os.getenv("SOTUHIRE_EXTENSION_IDS", "").split(",")
        if _EXTENSION_ID.fullmatch(value.strip())
    }
    extension_ids = configured or {DEFAULT_EXTENSION_ID}
    return frozenset(f"chrome-extension://{extension_id}" for extension_id in extension_ids)


def companion_origin_allowed(origin: str) -> bool:
    """Allow only the shipped extension identity or explicit local web origins."""
    return origin in _WEB_ORIGINS or origin in extension_origins()


def canonical_companion_origin(origin: str) -> str:
    """Return an allowlisted canonical value, never an untrusted reflected header."""
    if "\r" in origin or "\n" in origin:
        return ""
    for candidate in (*sorted(_WEB_ORIGINS), *sorted(extension_origins())):
        if origin == candidate:
            return candidate
    return ""


__all__ = [
    "DEFAULT_EXTENSION_ID",
    "canonical_companion_origin",
    "companion_origin_allowed",
    "extension_origins",
]
