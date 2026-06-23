"""Localhost-only HTTP server for the assistive browser companion."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from modules.local_api.app import LocalCompanionApp

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
_server: ThreadingHTTPServer | None = None
_thread: threading.Thread | None = None


class CompanionRequestHandler(BaseHTTPRequestHandler):
    """Translate local HTTP requests into LocalCompanionApp calls."""

    app = LocalCompanionApp()

    def do_OPTIONS(self) -> None:  # noqa: N802
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
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        status, payload = self.app.handle(
            self.command,
            self.path,
            body=body,
            client_host=self.client_address[0],
            token=self.headers.get("X-SotuHire-Token", ""),
        )
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-SotuHire-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


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
