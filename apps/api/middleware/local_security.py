"""Secure-by-default boundary for the SotuHire loopback API."""

from __future__ import annotations

import asyncio
import json
from http.cookies import SimpleCookie
from typing import Any

from modules.security import LocalAuthManager, LocalRateLimiter, RequestLimitError, RequestPolicy
from starlette.types import ASGIApp, Message, Receive, Scope, Send

SESSION_COOKIE = "sotuhire_local_session"
SAFE_METHODS = {"GET", "HEAD"}
PUBLIC_PATHS = {
    "/api/v1/health",
    "/api/v1/security/pairing/start",
    "/api/v1/security/pairing/complete",
    "/docs",
    "/docs/oauth2-redirect",
    "/openapi.json",
    "/redoc",
}


class LocalSecurityMiddleware:
    """Validate client, Host, Origin, authentication and bounded request shape."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        auth: LocalAuthManager,
        policy: RequestPolicy,
        allowed_origins: list[str],
        allowed_hosts: list[str],
    ) -> None:
        self.app = app
        self.auth = auth
        self.policy = policy
        self.allowed_origins = frozenset(allowed_origins)
        self.allowed_hosts = frozenset(host.casefold() for host in allowed_hosts)
        self.rate_limiter = LocalRateLimiter(
            requests=policy.rate_limit_requests,
            window_seconds=policy.rate_limit_window_seconds,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = _headers(scope)
        method = str(scope.get("method", "GET")).upper()
        path = str(scope.get("path", ""))
        origin = headers.get("origin", "")
        try:
            self._validate_client(scope)
            self._validate_host(headers.get("host", ""))
            self._validate_origin(origin)
            self._validate_rate(scope, path)
            if method == "OPTIONS":
                await self.app(scope, receive, send)
                return
            self._authenticate(method, path, origin, headers)
            body, replay = await self._bounded_body(method, headers, receive)
            self._validate_body(method, body, headers)
            async with asyncio.timeout(self.policy.timeout_seconds):
                await self.app(scope, replay, send)
        except RequestLimitError as exc:
            await _error(send, exc.status_code, exc.code, str(exc))
        except TimeoutError:
            await _error(send, 504, "request_timeout", "A requisição local excedeu o tempo limite.")

    def _validate_client(self, scope: Scope) -> None:
        client = scope.get("client")
        host = str(client[0]).casefold() if client else ""
        if host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
            raise RequestLimitError(
                "non_local_client", "A API local aceita somente clientes loopback.", status_code=403
            )

    def _validate_host(self, raw_host: str) -> None:
        host = raw_host.rsplit(":", 1)[0].strip("[]").casefold()
        if not host or host not in self.allowed_hosts:
            raise RequestLimitError(
                "invalid_host", "O Host informado não é aceito pela API local.", status_code=400
            )

    def _validate_origin(self, origin: str) -> None:
        if origin and origin not in self.allowed_origins:
            raise RequestLimitError(
                "origin_not_allowed", "A origem não está autorizada.", status_code=403
            )

    def _validate_rate(self, scope: Scope, path: str) -> None:
        client = scope.get("client")
        client_host = str(client[0]) if client else "unknown"
        if not self.rate_limiter.allow(f"{client_host}:{path}"):
            raise RequestLimitError(
                "rate_limit", "Muitas requisições locais; tente novamente.", status_code=429
            )

    def _authenticate(
        self, method: str, path: str, origin: str, headers: dict[str, str]
    ) -> None:
        if path in PUBLIC_PATHS:
            if path.startswith("/api/v1/security/") and not origin:
                raise RequestLimitError(
                    "pairing_origin_required",
                    "O pairing exige uma origem local autorizada.",
                    status_code=403,
                )
            return
        installation_token = headers.get("x-sotuhire-token", "")
        if self.auth.authenticate_installation(installation_token):
            return
        session_token = _cookie(headers.get("cookie", ""), SESSION_COOKIE)
        if self.auth.authenticate_session(
            session_token,
            origin=origin,
            csrf_token=headers.get("x-sotuhire-csrf", ""),
            require_csrf=method not in SAFE_METHODS,
        ):
            return
        raise RequestLimitError(
            "authentication_required",
            "Pareamento ou token local válido é obrigatório.",
            status_code=401,
        )

    async def _bounded_body(
        self, method: str, headers: dict[str, str], receive: Receive
    ) -> tuple[bytes, Receive]:
        if method in SAFE_METHODS or method == "OPTIONS":
            return b"", receive
        self.policy.validate_content_length(headers.get("content-length", ""))
        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.policy.max_body_bytes:
                raise RequestLimitError("body_too_large", "O corpo da requisição excede o limite.")
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if delivered:
                return {"type": "http.request", "body": b"", "more_body": False}
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        return body, replay

    def _validate_body(self, method: str, body: bytes, headers: dict[str, str]) -> None:
        if method in SAFE_METHODS or method == "OPTIONS" or not body:
            return
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        allowed = {"application/json", "multipart/form-data", "application/octet-stream"}
        if content_type not in allowed:
            raise RequestLimitError(
                "unsupported_content_type",
                "Content-Type não aceito.",
                status_code=415,
            )
        if content_type == "application/json":
            try:
                payload: Any = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                raise RequestLimitError(
                    "invalid_json", "O corpo JSON é inválido.", status_code=400
                ) from None
            self.policy.validate_json(payload)


def _headers(scope: Scope) -> dict[str, str]:
    return {
        key.decode("latin-1").casefold(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


def _cookie(raw_cookie: str, name: str) -> str:
    if not raw_cookie:
        return ""
    cookie = SimpleCookie()
    try:
        cookie.load(raw_cookie)
    except ValueError:
        return ""
    morsel = cookie.get(name)
    return morsel.value if morsel else ""


async def _error(send: Send, status_code: int, code: str, message: str) -> None:
    payload = json.dumps(
        {"error": {"code": code, "message": message, "details": {}}, "request_id": ""},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"content-length", str(len(payload)).encode("ascii")),
                (b"cache-control", b"no-store"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": payload})


__all__ = ["LocalSecurityMiddleware", "SESSION_COOKIE"]
