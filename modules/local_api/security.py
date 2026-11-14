"""Security helpers for the localhost-only companion API."""

from __future__ import annotations

import os
from ipaddress import ip_address


def is_local_client(host: str) -> bool:
    """Return whether an incoming socket address is loopback."""
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return host.casefold() == "localhost"


def configured_token() -> str:
    """Return an explicitly configured local companion installation token."""
    return os.getenv("SOTUHIRE_COMPANION_TOKEN", "").strip()


def sanitize_text(value: str, *, limit: int) -> str:
    """Remove control characters and cap locally persisted visible text."""
    clean = "".join(character for character in value if character in "\n\t" or ord(character) >= 32)
    return clean.strip()[:limit]
