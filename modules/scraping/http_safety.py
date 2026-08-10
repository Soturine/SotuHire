"""SSRF-resistant URL and redirect validation for public-source connectors."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable, Iterable
from urllib.parse import ParseResult, urlparse
from urllib.request import HTTPRedirectHandler, OpenerDirector, build_opener

Resolver = Callable[[str, int], Iterable[str]]


class UnsafePublicUrl(ValueError):
    """Raised before a connector reaches a non-public network target."""


def validate_public_url(
    value: str,
    *,
    resolve: bool = False,
    resolver: Resolver | None = None,
) -> ParseResult:
    """Validate scheme, authority, port and, when requested, every resolved IP."""
    parsed = urlparse(value.strip())
    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafePublicUrl("A URL publica possui uma porta invalida.") from exc
    hostname = (parsed.hostname or "").rstrip(".").casefold()
    if parsed.scheme.casefold() not in {"http", "https"} or not hostname:
        raise UnsafePublicUrl("Informe uma URL publica HTTP ou HTTPS.")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafePublicUrl("URLs publicas nao podem conter credenciais.")
    if port not in {None, 80, 443}:
        raise UnsafePublicUrl("A coleta publica aceita somente as portas 80 e 443.")
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise UnsafePublicUrl("A coleta publica nao acessa enderecos locais.")
    _require_global_address(hostname)
    if resolve:
        resolved = list((resolver or _resolve_addresses)(hostname, port or _default_port(parsed)))
        if not resolved:
            raise UnsafePublicUrl("O host publico nao pode ser resolvido.")
        for address in resolved:
            _require_global_address(address)
    return parsed


def safe_public_opener() -> OpenerDirector:
    """Return an opener that validates every redirect before following it."""
    return build_opener(ValidatingRedirectHandler())


class ValidatingRedirectHandler(HTTPRedirectHandler):
    """Reject redirects to credentials, local services or non-public addresses."""

    max_redirections = 5
    max_repeats = 2

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN201
        validate_public_url(newurl, resolve=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _default_port(parsed: ParseResult) -> int:
    return 443 if parsed.scheme.casefold() == "https" else 80


def _resolve_addresses(hostname: str, port: int) -> list[str]:
    try:
        records = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafePublicUrl("O host publico nao pode ser resolvido.") from exc
    return list(dict.fromkeys(str(record[4][0]) for record in records))


def _require_global_address(value: str) -> None:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return
    if not address.is_global:
        raise UnsafePublicUrl("A coleta publica nao acessa enderecos locais ou privados.")


__all__ = [
    "UnsafePublicUrl",
    "ValidatingRedirectHandler",
    "safe_public_opener",
    "validate_public_url",
]
