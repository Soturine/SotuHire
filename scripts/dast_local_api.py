"""Dynamic security probes against a running Local API (C13).

    python scripts/run_api.py &                       # synthetic SOTUHIRE_DATA_DIR
    python scripts/dast_local_api.py [--base http://127.0.0.1:8787]

Black-box checks over real HTTP, no credentials: what a hostile web page or a DNS-rebinding attempt
could do to a local-first API. Each probe states the expected refusal; the report lists every probe
with its observed status and exits 1 if any expectation fails. Nothing is written to the data dir
except by probes that must be refused.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import urllib.error
import urllib.request

EVIL_ORIGIN = "https://evil.example"


def request(base: str, method: str, path: str, *, headers=None, body: bytes | None = None):
    req = urllib.request.Request(base + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:  # noqa: S310 - loopback only
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8787")
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
        headers=json_headers,
        body=json.dumps({"challenge_id": "x" * 20, "proof": "y" * 20}).encode(),
    )
    probe("forged pairing proof", "refused (4xx)", 400 <= status < 500, status)

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

    # A large body without a session is refused before it is read (auth before parse).
    try:
        status, _, _ = request(
            base,
            "POST",
            "/api/v1/profile/import-text",
            headers=json_headers,
            body=b'{"text": "' + b"a" * (6 * 1024 * 1024) + b'"}',
        )
        probe("large body without session", "401, body not parsed", status == 401, status)
    except ConnectionError:
        probe(
            "large body without session",
            "401, body not parsed",
            True,
            0,
            "server answered and closed before the body was sent",
        )

    for path in (
        "/api/v1/data/backups/..%2F..%2Fsotuhire.db",
        "/api/v1/data/backups/%2e%2e%5csotuhire.db",
        "/api/v1/data/backups/sotuhire.db",
    ):
        status, _, body = request(base, "GET", path)
        probe(
            f"traversal {path}",
            "refused, never the database",
            status in (400, 401, 404, 422) and b"SQLite format" not in body,
            status,
        )

    status, _, body = request(base, "GET", "/api/v1/does-not-exist")
    text = body.decode("utf-8", "replace")
    leak = re.search(r"[A-Za-z]:\\\\|/Users/|/home/|AppData", text)
    probe(
        "error bodies leak no local path",
        "no absolute path in error",
        leak is None,
        status,
        text[:120],
    )

    ok = all(result["ok"] for result in results)
    print(json.dumps({"base": base, "ok": ok, "probes": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
