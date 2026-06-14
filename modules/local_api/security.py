"""Security helpers for the localhost-only companion API."""

from __future__ import annotations

import hmac
import os
from ipaddress import ip_address

MAX_LOG_TEXT = 160


def is_local_client(host: str) -> bool:
    """Return whether an incoming socket address is loopback."""
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return host.casefold() == "localhost"


def configured_token() -> str:
    """Return the optional local companion token."""
    return os.getenv("SOTUHIRE_COMPANION_TOKEN", "").strip()


def token_is_valid(provided: str, expected: str | None = None) -> bool:
    """Require a matching token only when one is configured."""
    required = configured_token() if expected is None else expected
    return not required or hmac.compare_digest(provided, required)


def sanitize_text(value: str, *, limit: int) -> str:
    """Remove control characters and cap locally persisted visible text."""
    clean = "".join(character for character in value if character in "\n\t" or ord(character) >= 32)
    return clean.strip()[:limit]


def safe_log_label(value: str) -> str:
    """Return a short single-line label suitable for minimal logs."""
    return sanitize_text(value, limit=MAX_LOG_TEXT).replace("\n", " ")
