"""SSRF-resistant URL and redirect validation for public-source connectors."""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from email.message import Message
from urllib.parse import ParseResult, urljoin, urlparse

Resolver = Callable[[str, int], Iterable[str]]
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class UnsafePublicUrl(ValueError):
    """Raised before a connector reaches a non-public network target."""


@dataclass(frozen=True)
class ResolvedPublicUrl:
    """Canonical public URL whose addresses were checked before connection."""

    url: str
    parsed: ParseResult
    hostname: str
    port: int
    addresses: tuple[str, ...]


@dataclass(frozen=True)
class PublicHttpResponse:
    """Bounded response returned by the pinned public transport."""

    url: str
    status: int
    headers: Message
    body: bytes


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
    hostname = _canonical_hostname(parsed.hostname or "")
    if parsed.scheme.casefold() not in {"http", "https"} or not hostname:
        raise UnsafePublicUrl("Informe uma URL publica HTTP ou HTTPS.")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafePublicUrl("URLs publicas nao podem conter credenciais.")
    if port not in {None, 80, 443}:
        raise UnsafePublicUrl("A coleta publica aceita somente as portas 80 e 443.")
    if port is not None and port != _default_port(parsed):
        raise UnsafePublicUrl("A porta publica deve corresponder ao protocolo informado.")
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


def resolve_public_url(value: str, *, resolver: Resolver | None = None) -> ResolvedPublicUrl:
    """Resolve once and retain the exact global addresses allowed for the connection."""
    parsed = validate_public_url(value)
    hostname = _canonical_hostname(parsed.hostname or "")
    port = parsed.port or _default_port(parsed)
    addresses = tuple((resolver or _resolve_addresses)(hostname, port))
    if not addresses:
        raise UnsafePublicUrl("O host publico nao pode ser resolvido.")
    canonical_addresses: list[str] = []
    for address in addresses:
        canonical = str(ipaddress.ip_address(address))
        _require_global_address(canonical)
        if canonical not in canonical_addresses:
            canonical_addresses.append(canonical)
    return ResolvedPublicUrl(
        url=parsed.geturl(),
        parsed=parsed,
        hostname=hostname,
        port=port,
        addresses=tuple(canonical_addresses),
    )


def request_public_url(
    value: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 15,
    max_bytes: int = 2_000_000,
    resolver: Resolver | None = None,
    max_redirects: int = 5,
) -> PublicHttpResponse:
    """Fetch through an IP-pinned socket, re-resolving and revalidating every redirect."""
    current = value
    previous_scheme = ""
    for redirect_count in range(max_redirects + 1):
        target = resolve_public_url(current, resolver=resolver)
        scheme = target.parsed.scheme.casefold()
        if previous_scheme == "https" and scheme != "https":
            raise UnsafePublicUrl("Redirect HTTPS para HTTP nao e permitido.")
        response = _request_pinned(target, headers or {}, timeout=timeout, max_bytes=max_bytes)
        if response.status not in REDIRECT_STATUSES:
            return response
        if redirect_count == max_redirects:
            raise UnsafePublicUrl("A URL publica excedeu o limite de redirects.")
        location = response.headers.get("Location", "").strip()
        if not location or "\r" in location or "\n" in location:
            raise UnsafePublicUrl("Redirect publico invalido.")
        previous_scheme = scheme
        current = urljoin(target.url, location)
    raise UnsafePublicUrl("A URL publica excedeu o limite de redirects.")


def _request_pinned(
    target: ResolvedPublicUrl,
    headers: dict[str, str],
    *,
    timeout: float,
    max_bytes: int,
) -> PublicHttpResponse:
    last_error: OSError | None = None
    path = target.parsed.path or "/"
    if target.parsed.params:
        path += f";{target.parsed.params}"
    if target.parsed.query:
        path += f"?{target.parsed.query}"
    request_headers = {key: _safe_header_value(value) for key, value in headers.items()}
    request_headers["Host"] = target.hostname
    for address in target.addresses:
        connection: http.client.HTTPConnection
        if target.parsed.scheme.casefold() == "https":
            connection = _PinnedHTTPSConnection(
                target.hostname,
                target.port,
                address,
                timeout=timeout,
            )
        else:
            connection = _PinnedHTTPConnection(
                target.hostname,
                target.port,
                address,
                timeout=timeout,
            )
        try:
            connection.request("GET", path, headers=request_headers)
            raw = connection.getresponse()
            body = raw.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError("Resposta excede o limite seguro de coleta.")
            return PublicHttpResponse(
                url=target.url,
                status=raw.status,
                headers=raw.headers,
                body=body,
            )
        except OSError as exc:
            last_error = exc
        finally:
            connection.close()
    if last_error is not None:
        raise last_error
    raise UnsafePublicUrl("Nenhum endereco publico validado ficou disponivel.")


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, pinned_address: str, *, timeout: float) -> None:
        super().__init__(host, port=port, timeout=timeout)
        self._pinned_address = pinned_address

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
            self.source_address,
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, pinned_address: str, *, timeout: float) -> None:
        super().__init__(host, port=port, timeout=timeout, context=ssl.create_default_context())
        self._pinned_address = pinned_address

    def connect(self) -> None:
        sock = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
            self.source_address,
        )
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


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
    mapped = address.ipv4_mapped if isinstance(address, ipaddress.IPv6Address) else None
    if not address.is_global or (mapped is not None and not mapped.is_global):
        raise UnsafePublicUrl("A coleta publica nao acessa enderecos locais ou privados.")


def _canonical_hostname(value: str) -> str:
    hostname = value.rstrip(".").casefold()
    if not hostname:
        return ""
    try:
        return hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise UnsafePublicUrl("O hostname publico e invalido.") from exc


def _safe_header_value(value: str) -> str:
    if "\r" in value or "\n" in value:
        raise UnsafePublicUrl("Header de coleta publica invalido.")
    return value


__all__ = [
    "UnsafePublicUrl",
    "PublicHttpResponse",
    "ResolvedPublicUrl",
    "request_public_url",
    "resolve_public_url",
    "validate_public_url",
]
