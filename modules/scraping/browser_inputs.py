"""Validation boundary for values passed to the protected browser launcher."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def validate_browser_start_url(value: str) -> str:
    """Return a browser URL that cannot be interpreted as a Chromium option."""
    cleaned = value.strip()
    if not cleaned or cleaned.startswith("-") or "\r" in cleaned or "\n" in cleaned:
        raise ValueError("URL inicial do navegador invalida.")
    parsed = urlparse(cleaned)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("A URL inicial deve usar HTTP ou HTTPS.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("A URL inicial nao pode conter credenciais.")
    return cleaned


def validate_local_cdp_url(value: str) -> str:
    """Allow only an explicit loopback HTTP CDP endpoint."""
    cleaned = value.strip()
    if not cleaned or cleaned.startswith("-") or "\r" in cleaned or "\n" in cleaned:
        raise ValueError("Endpoint CDP invalido.")
    parsed = urlparse(cleaned)
    if parsed.scheme.casefold() != "http" or parsed.username is not None or parsed.password is not None:
        raise ValueError("O endpoint CDP deve usar HTTP local sem credenciais.")
    hostname = (parsed.hostname or "").rstrip(".").casefold()
    try:
        is_loopback = hostname == "localhost" or ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        is_loopback = False
    if not is_loopback or parsed.port != 9222 or parsed.path not in {"", "/"} or parsed.query:
        raise ValueError("O endpoint CDP permitido e o loopback local na porta 9222.")
    return cleaned


__all__ = ["validate_browser_start_url", "validate_local_cdp_url"]
