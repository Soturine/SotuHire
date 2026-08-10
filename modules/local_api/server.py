"""Localhost-only HTTP server for the assistive browser companion."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import cast

from modules.local_api.app import LocalCompanionApp
from modules.local_api.origins import canonical_companion_origin, companion_origin_allowed
from modules.security import LocalRateLimiter, RequestLimitError, RequestPolicy

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
_server: ThreadingHTTPServer | None = None
_thread: threading.Thread | None = None


class CompanionRequestHandler(BaseHTTPRequestHandler):
    """Translate local HTTP requests into LocalCompanionApp calls."""

    app = LocalCompanionApp()
    policy = RequestPolicy(max_body_bytes=1_048_576, max_batch_items=100, max_json_depth=16)
    rate_limiter = LocalRateLimiter(requests=120, window_seconds=60)

    def do_OPTIONS(self) -> None:  # noqa: N802
        error = self._boundary_error()
        if error:
            self._send_json(*error)
            return
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        self._handle()

    def do_POST(self) -> None:  # noqa: N802
        self._handle()

    def log_message(self, format: str, *args: object) -> None:
        return

    def _handle(self) -> None:
        error = self._boundary_error()
        if error:
            self._send_json(*error)
            return
        try:
            raw_length = self.headers.get("Content-Length", "")
            self.policy.validate_content_length(raw_length)
            length = int(raw_length or "0")
            if self.command == "POST":
                content_type = self.headers.get("Content-Type", "").split(";", 1)[0].casefold()
                if content_type != "application/json":
                    self._send_json(415, {"ok": False, "message": "Content-Type não aceito."})
                    return
            self.connection.settimeout(self.policy.timeout_seconds)
            body = self.rfile.read(length) if length else b""
            if body:
                self.policy.validate_json(json.loads(body))
        except (RequestLimitError, json.JSONDecodeError, RecursionError) as exc:
            status = exc.status_code if isinstance(exc, RequestLimitError) else 400
            self._send_json(status, {"ok": False, "message": "Payload local inválido."})
            return
        except TimeoutError:
            self._send_json(408, {"ok": False, "message": "Tempo limite da requisição excedido."})
            return
        status, payload = self.app.handle(
            self.command,
            self.path,
            body=body,
            client_host=self.client_address[0],
            token=self.headers.get("X-SotuHire-Token", ""),
            origin=self.headers.get("Origin", ""),
            idempotency_key=self.headers.get("X-SotuHire-Idempotency-Key", ""),
        )
        self._send_json(status, payload)

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _boundary_error(self) -> tuple[int, dict[str, object]] | None:
        host = self.headers.get("Host", "").casefold()
        server_address = cast(tuple[str, int], self.server.server_address)
        port = server_address[1]
        allowed_hosts = {
            f"127.0.0.1:{port}",
            f"localhost:{port}",
            f"[::1]:{port}",
        }
        if host not in allowed_hosts:
            return 400, {"ok": False, "message": "Host local inválido."}
        origin = self.headers.get("Origin", "")
        if origin and not _origin_allowed(origin):
            return 403, {"ok": False, "message": "Origem não autorizada."}
        key = f"{self.client_address[0]}:{self.path}"
        if not self.rate_limiter.allow(key):
            return 429, {"ok": False, "message": "Muitas requisições locais."}
        return None

    def _cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        allowed_origin = canonical_companion_origin(origin)
        if allowed_origin:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Vary", "Origin")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, X-SotuHire-Token, X-SotuHire-Idempotency-Key",
        )
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Cache-Control", "no-store")


def _origin_allowed(origin: str) -> bool:
    return companion_origin_allowed(origin)


def start_server(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    app: LocalCompanionApp | None = None,
) -> ThreadingHTTPServer:
    """Start the local companion in a daemon thread."""
    global _server, _thread
    if host != DEFAULT_HOST:
        raise ValueError("A Local Companion API deve usar 127.0.0.1.")
    if _server is not None:
        return _server
    if app is not None:
        CompanionRequestHandler.app = app
    _server = ThreadingHTTPServer((host, port), CompanionRequestHandler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    return _server


def stop_server() -> None:
    """Stop the current local companion server."""
    global _server, _thread
    if _server is not None:
        _server.shutdown()
        _server.server_close()
    _server = None
    _thread = None


def server_status() -> dict[str, object]:
    """Return safe runtime status without secrets."""
    return {
        "running": _server is not None,
        "host": DEFAULT_HOST,
        "port": _server.server_port if _server is not None else DEFAULT_PORT,
    }


def run_forever() -> None:
    """Run the local companion server until interrupted."""
    start_server()
    print(f"SotuHire Local Companion API: http://{DEFAULT_HOST}:{DEFAULT_PORT}/health")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_server()


if __name__ == "__main__":
    run_forever()
