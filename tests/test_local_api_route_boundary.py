"""The Local Companion's authentication boundary, route by route.

Pins LocalCompanionApp.handle: only the paths in PUBLIC_PATHS answer without a credential; every
route of the canonical AUTHENTICATED_ROUTES table answers 401 without one, whatever the body (an
invalid, non-UTF-8, oversized or deeply nested body included: content from an unauthenticated
caller is never parsed); an unknown path answers 404 only after authentication, so it does not
reveal which paths exist; a known path with the wrong method is 405.

The test walks the table the app dispatches from instead of a copy of it, and checks the other
direction too: every path the shipped extension calls is a declared route.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from modules.local_api import LocalCompanionApp
from modules.local_api.app import AUTHENTICATED_ROUTES, PUBLIC_PATHS, LocalCompanionService
from modules.local_api.origins import DEFAULT_EXTENSION_ID
from modules.security import RequestPolicy

ROOT = Path(__file__).resolve().parents[1]
ROUTES = sorted((route.method, path) for path, route in AUTHENTICATED_ROUTES.items())
WRITES = [(method, path) for method, path in ROUTES if method == "POST"]
EXTENSION_ORIGIN = f"chrome-extension://{DEFAULT_EXTENSION_ID}"
DEEP = b'{"a":' * 40 + b"1" + b"}" * 40
HOSTILE_BODIES = {
    "empty": b"",
    "object": b"{}",
    "invalid-json": b"{not json",
    "not-utf8": b"\xff\xfe\x00",
    "array": b"[]",
    "deep": DEEP,
}


@pytest.fixture
def app() -> LocalCompanionApp:
    return LocalCompanionApp(token="local-secret")


def test_the_public_surface_is_exactly_health_and_pairing():
    # Widening this set makes a route reachable without a credential: a reviewed change.
    assert frozenset({"/health", "/pairing/start", "/pairing/complete"}) == PUBLIC_PATHS
    assert not PUBLIC_PATHS & AUTHENTICATED_ROUTES.keys()


def test_every_route_names_a_real_handler_and_a_body_model_only_for_writes():
    for path, route in AUTHENTICATED_ROUTES.items():
        assert callable(getattr(LocalCompanionService, route.handler, None)), path
        assert route.method in {"GET", "POST"}, path
        assert (route.request_model is None) == (route.method == "GET"), path


def test_every_path_the_extension_calls_is_a_declared_route():
    called: set[str] = set()
    for source in (ROOT / "browser-extension").glob("*.js"):
        called |= set(
            re.findall(
                r"[\"'`](/(?:capture/[a-z-]+|handshake|pairing/[a-z]+|health))[\"'`]",
                source.read_text(encoding="utf-8"),
            )
        )
    assert called, "the pattern no longer finds the extension's calls"
    assert called <= PUBLIC_PATHS | AUTHENTICATED_ROUTES.keys(), called - (
        PUBLIC_PATHS | AUTHENTICATED_ROUTES.keys()
    )


@pytest.mark.parametrize(("method", "path"), ROUTES)
@pytest.mark.parametrize("body", HOSTILE_BODIES.values(), ids=HOSTILE_BODIES.keys())
def test_without_a_credential_every_route_is_401_whatever_the_body(app, method, path, body):
    for token in ("", "wrong"):
        status, payload = app.handle(method, path, body=body, token=token)
        assert status == 401, (method, path, token, body[:12])
        assert payload["ok"] is False


@pytest.mark.parametrize(("method", "path"), ROUTES)
def test_authenticated_routes_reach_validation_or_a_result(app, method, path):
    status, _ = app.handle(method, path, body=b"{}", token="local-secret")
    # 404 here is a domain lookup ("Captura não encontrada"), not an unknown route
    assert status in {200, 404, 422}, (method, path, status)


@pytest.mark.parametrize(("method", "path"), WRITES)
def test_after_authentication_a_malformed_body_is_rejected_without_reaching_the_handler(
    app, method, path, monkeypatch
):
    route = AUTHENTICATED_ROUTES[path]
    monkeypatch.setattr(
        app.service, route.handler, lambda *_: pytest.fail("handler reached with a bad body")
    )
    for body, expected in (
        (b"{not json", 400),
        (b"\xff\xfe\x00", 400),
        (b"[]", 422),
        (DEEP, 422),
    ):
        status, payload = app.handle(method, path, body=body, token="local-secret")
        assert status == expected, (path, body[:12], status, payload)


def test_a_body_over_the_limit_is_413_before_authentication_or_parsing():
    app = LocalCompanionApp(token="local-secret", policy=RequestPolicy(max_body_bytes=64))
    big = b'{"x":"' + b"a" * 100 + b'"}'
    assert app.handle("POST", "/capture/job", body=big)[0] == 413
    assert app.handle("POST", "/capture/job", body=big, token="local-secret")[0] == 413
    assert app.handle("POST", "/pairing/complete", body=big, origin=EXTENSION_ORIGIN)[0] == 413


def test_a_batch_over_the_limit_is_422_after_authentication():
    app = LocalCompanionApp(token="local-secret", policy=RequestPolicy(max_batch_items=2))
    body = json.dumps({"applications": [{}, {}, {}]}).encode()
    assert app.handle("POST", "/capture/applications", body=body)[0] == 401
    assert app.handle("POST", "/capture/applications", body=body, token="local-secret")[0] == 422


def test_public_routes_answer_without_a_credential(app):
    assert app.handle("GET", "/health")[0] == 200
    # pairing still checks the origin; an unknown origin is refused, not asked for a token
    assert app.handle("POST", "/pairing/start", body=b"{}", origin="https://evil.example")[0] == 403
    assert app.handle("POST", "/pairing/start", origin=EXTENSION_ORIGIN)[0] == 200


def test_pairing_complete_rejects_a_non_object_body_instead_of_crashing(app):
    for body, expected in ((b"[]", 422), (b"{not json", 400), (b"\xff", 400)):
        status, payload = app.handle(
            "POST", "/pairing/complete", body=body, origin=EXTENSION_ORIGIN
        )
        assert status == expected and payload["ok"] is False, (body, status)


def test_public_paths_with_the_wrong_method_are_405(app):
    assert app.handle("POST", "/health")[0] == 405
    assert app.handle("GET", "/pairing/start", origin=EXTENSION_ORIGIN)[0] == 405


def test_unknown_paths_are_hidden_behind_authentication(app):
    assert app.handle("POST", "/capture/unknown", body=b"{not json")[0] == 401
    assert app.handle("POST", "/capture/unknown", body=b"{}", token="local-secret")[0] == 404


def test_a_known_path_with_the_wrong_method_is_405(app):
    status, payload = app.handle("DELETE", "/capture/job", token="local-secret")
    assert status == 405 and payload["ok"] is False


def test_non_local_clients_are_refused_before_anything_else(app):
    assert app.handle("GET", "/health", client_host="10.0.0.5")[0] == 403


def test_over_a_real_socket_an_unauthenticated_bad_body_is_401_not_a_parse_error(tmp_path):
    """The HTTP layer only bounds and reads bytes; it no longer parses JSON before auth."""
    import http.client
    import threading
    from http.server import ThreadingHTTPServer

    from modules.local_api.server import CompanionRequestHandler

    handler = type(
        "Handler", (CompanionRequestHandler,), {"app": LocalCompanionApp(token="local-secret")}
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]

        def post(body: bytes, token: str = "") -> int:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            headers = {"Content-Type": "application/json", "Host": f"127.0.0.1:{port}"}
            if token:
                headers["X-SotuHire-Token"] = token
            connection.request("POST", "/capture/job", body=body, headers=headers)
            status = connection.getresponse().status
            connection.close()
            return status

        assert post(b"{not json") == 401
        assert post(DEEP) == 401
        assert post(b"{not json", token="local-secret") == 400
        assert post(DEEP, token="local-secret") == 422
    finally:
        server.shutdown()
        server.server_close()
