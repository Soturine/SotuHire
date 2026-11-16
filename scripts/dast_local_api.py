"""Dynamic security probes against a running Local API (C13).

    python scripts/run_api.py &                       # synthetic SOTUHIRE_DATA_DIR
    python scripts/dast_local_api.py [--base http://127.0.0.1:8787]

Black-box checks over real HTTP: what a hostile web page or a DNS-rebinding attempt could do to a
local-first API. Each probe states the expected refusal; the report lists every probe with its
observed status and exits 1 if any expectation fails. A probe whose outcome cannot be observed (the
connection drops before any answer) fails as inconclusive: silence is not a refusal.

    python scripts/dast_local_api.py --bootstrap "$SOTUHIRE_PAIRING_BOOTSTRAP"

With the pairing bootstrap, the probes also pair a session like the web app does and repeat the
path-traversal checks with it, so they reach the archive resolver instead of stopping at the 401.
That run creates one backup archive: use a disposable SOTUHIRE_DATA_DIR, never real data.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

EVIL_ORIGIN = "https://evil.example"
LOCAL_ORIGIN = "http://127.0.0.1:5173"  # an origin the API allows by default (apps/api/config.py)
LEAK = re.compile(r"[A-Za-z]:\\\\|/Users/|/home/|AppData|sotuhire-data[/\\]")


def request(base: str, method: str, path: str, *, headers=None, body: bytes | None = None):
    req = urllib.request.Request(base + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:  # noqa: S310 - loopback only
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def header(headers: dict, name: str) -> str:
    return next((value for key, value in headers.items() if key.lower() == name), "")


def answer_before_body(base: str, path: str, total: int, sent_first: int = 64 * 1024):
    """Announce `total` bytes, send only the first `sent_first`, then read what the server says.

    Returns (status line or "", bytes sent). An empty status line means nothing was observed."""
    parts = urllib.parse.urlsplit(base)
    host, port = parts.hostname or "127.0.0.1", parts.port or 80
    head = (
        f"POST {path} HTTP/1.1\r\nHost: {host}:{port}\r\nContent-Type: application/json\r\n"
        f"Content-Length: {total}\r\nConnection: close\r\n\r\n"
    )
    data = b""
    with socket.create_connection((host, port), timeout=10) as sock:
        sock.sendall(head.encode("ascii") + b"a" * sent_first)
        sock.settimeout(5)
        try:
            data = sock.recv(4096)
        except OSError:  # timeout or reset: nothing observed
            data = b""
    status_line = data.split(b"\r\n", 1)[0].decode("latin-1") if data else ""
    return status_line, sent_first


def pair_session(base: str, bootstrap: str):
    """Pair like the web app: bootstrap -> challenge -> session cookie + CSRF token."""
    origin = {"content-type": "application/json", "Origin": LOCAL_ORIGIN}
    status, _, body = request(
        base,
        "POST",
        "/api/v1/security/pairing/start",
        headers={**origin, "x-sotuhire-pairing-bootstrap": bootstrap},
        body=json.dumps({"client_kind": "web", "client_name": "DAST probe"}).encode(),
    )
    if status != 200:
        return None, f"pairing/start answered {status}"
    challenge = json.loads(body)["data"]
    status, headers, body = request(
        base,
        "POST",
        "/api/v1/security/pairing/complete",
        headers=origin,
        body=json.dumps(
            {"challenge_id": challenge["challenge_id"], "proof": challenge["proof"]}
        ).encode(),
    )
    cookie = header(headers, "set-cookie").split(";", 1)[0]
    if status != 200 or not cookie:
        return None, f"pairing/complete answered {status}"
    csrf = json.loads(body)["data"]["csrf_token"]
    return {"Origin": LOCAL_ORIGIN, "Cookie": cookie, "X-SotuHire-CSRF": csrf}, "paired"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8787")
    parser.add_argument(
        "--bootstrap",
        default="",
        help="pairing bootstrap of a disposable instance; adds the authorized-session probes",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")
    json_headers = {"content-type": "application/json"}
    results = []

    def probe(name: str, expectation: str, ok: bool, status: int, detail: str = "") -> None:
        results.append(
            {"probe": name, "expect": expectation, "status": status, "ok": ok, "detail": detail}
        )

    status, headers, _ = request(base, "GET", "/api/v1/health")
    probe("health reachable", "200", status == 200, status)

    status, headers, _ = request(base, "GET", "/api/v1/health", headers={"Host": "evil.example"})
    probe("DNS rebinding Host", "400 for a foreign Host", status == 400, status)

    status, headers, _ = request(base, "GET", "/api/v1/profile", headers={"Origin": EVIL_ORIGIN})
    allow = headers.get(
        "access-control-allow-origin", headers.get("Access-Control-Allow-Origin", "")
    )
    probe(
        "foreign Origin read",
        "refused and no CORS grant",
        status in (401, 403) and allow != EVIL_ORIGIN,
        status,
        f"allow-origin={allow!r}",
    )

    status, headers, _ = request(
        base,
        "OPTIONS",
        "/api/v1/profile",
        headers={
            "Origin": EVIL_ORIGIN,
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    allow = headers.get(
        "access-control-allow-origin", headers.get("Access-Control-Allow-Origin", "")
    )
    probe(
        "foreign preflight",
        "no CORS grant",
        allow != EVIL_ORIGIN,
        status,
        f"allow-origin={allow!r}",
    )

    for method, path in (
        ("GET", "/api/v1/profile"),
        ("PUT", "/api/v1/profile"),
        ("GET", "/api/v2/approvals"),
    ):
        status, _, _ = request(
            base, method, path, headers=json_headers, body=b"{}" if method != "GET" else None
        )
        probe(f"no session {method} {path}", "401", status == 401, status)

    status, _, _ = request(
        base,
        "POST",
        "/api/v1/security/pairing/complete",
        # An allowed Origin, so the request reaches the proof check (without one the origin gate
        # answers 403 first and the proof is never examined).
        headers={**json_headers, "Origin": LOCAL_ORIGIN},
        body=json.dumps({"challenge_id": "x" * 20, "proof": "y" * 20}).encode(),
    )
    probe("forged pairing proof", "401 from the proof check", status == 401, status)

    # Announce a 13 MB body (limit 12 MB) without sending it: the refusal must come from the
    # header alone, before anything is read (sending it would only show the connection closing).
    host = base.split("//", 1)[1]
    connection = http.client.HTTPConnection(host, timeout=10)
    connection.putrequest("POST", "/api/v1/profile/import-text")
    connection.putheader("content-type", "application/json")
    connection.putheader("content-length", str(13 * 1024 * 1024))
    connection.endheaders()
    response = connection.getresponse()
    # This API authenticates before it looks at the size (the Companion checks size first); both
    # orders are safe as long as nothing is read before the refusal, which the next probe shows.
    probe(
        "oversized body (declared)",
        "refused from the headers alone (401 without session, 413 with one)",
        response.status in (401, 413),
        response.status,
    )
    connection.close()

    # A large body without a session is refused before it is read (auth before parse). Only 64 KB
    # of the 6 MB are sent; a 401 status line read back proves the answer came first. No answer
    # (timeout, reset) is inconclusive and fails: it does not show what the server did.
    total = 6 * 1024 * 1024
    status_line, sent = answer_before_body(base, "/api/v1/profile/import-text", total)
    fields = status_line.split()
    observed = int(fields[1]) if len(fields) > 1 and fields[1].isdigit() else 0
    probe(
        "large body without session",
        "401 answered after 64 KB of 6 MB, body not read",
        observed == 401,
        observed,
        f"{status_line or 'no answer: inconclusive'}; sent {sent} of {total} bytes",
    )

    traversal_paths = (
        "/api/v1/data/backups/..%2F..%2Fsotuhire.db",
        "/api/v1/data/backups/%2e%2e%5csotuhire.db",
        "/api/v1/data/backups/sotuhire.db",
        "/api/v1/data/backups/..%2Fsotuhire-data-x.zip",
        "/api/v1/data/backups/C%3A%5CWindows%5Cwin.ini",
    )
    for path in traversal_paths:
        status, _, body = request(base, "GET", path)
        probe(
            f"traversal without session {path}",
            "401 (refused before the resolver)",
            status == 401 and b"SQLite format" not in body,
            status,
        )

    if args.bootstrap:
        session, detail = pair_session(base, args.bootstrap)
        probe("authorized session paired", "200 + session cookie", session is not None, 0, detail)
        if session is not None:
            status, _, _ = request(base, "GET", "/api/v1/profile", headers=session)
            probe("session reaches a protected route", "200", status == 200, status)
            # Positive control: a real archive downloads with this session, so a refusal below is
            # the resolver's, not a missing session's.
            status, _, body = request(
                base,
                "POST",
                "/api/v1/data/backups",
                headers={**session, "content-type": "application/json"},
                body=b'{"kind": "backup"}',
            )
            name = json.loads(body)["data"]["archive_name"] if status == 200 else ""
            probe("session creates a backup", "200", status == 200, status, name)
            if name:
                status, _, body = request(
                    base, "GET", f"/api/v1/data/backups/{name}", headers=session
                )
                probe(
                    "session downloads its own archive",
                    "200, a ZIP",
                    status == 200 and body[:2] == b"PK",
                    status,
                )
            for path in traversal_paths:
                status, _, body = request(base, "GET", path, headers=session)
                probe(
                    f"traversal with session {path}",
                    # 400: the resolver rejects the name; 404: routing never matched (an encoded
                    # slash) or no such archive. Either way no file is served.
                    "400/404, never a file",
                    status in (400, 404)
                    and b"SQLite format" not in body
                    and body[:2] != b"PK"
                    and b"[fonts]" not in body,
                    status,
                )
            # Errors raised past authentication, where the handlers' own messages are returned.
            for path in (
                "/api/v1/data/backups/sotuhire-data-backup-19990101-000000.zip",
                "/api/v1/does-not-exist",
            ):
                status, _, body = request(base, "GET", path, headers=session)
                text = body.decode("utf-8", "replace")
                probe(
                    f"session error {path} leaks no local path",
                    "404, no absolute path",
                    status == 404 and LEAK.search(text) is None,
                    status,
                    text[:120],
                )

    status, _, body = request(base, "GET", "/api/v1/does-not-exist")
    text = body.decode("utf-8", "replace")
    probe(
        "error bodies leak no local path",
        "no absolute path in error",
        LEAK.search(text) is None,
        status,
        text[:120],
    )

    ok = all(result["ok"] for result in results)
    print(json.dumps({"base": base, "ok": ok, "probes": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
