"""The Local Companion's authentication boundary, route by route.

Pins the behaviour of LocalCompanionApp.handle before and after it became a route table: only
/health and the two pairing routes answer without a credential; every other route answers 401
without one, whatever the body; an unknown path answers 404 only after authentication, so it does
not reveal which paths exist; a known path with the wrong method is 405.
"""

from __future__ import annotations

import pytest
from modules.local_api import LocalCompanionApp

AUTHENTICATED = [
    ("GET", "/capture/status"),
    ("GET", "/capture/context-summary"),
    ("POST", "/handshake"),
    ("POST", "/capture/job"),
    ("POST", "/capture/public-exam"),
    ("POST", "/capture/analyze"),
    ("POST", "/capture/tracker"),
    ("POST", "/capture/applications"),
    ("POST", "/capture/github-profile"),
    ("POST", "/capture/github-repo"),
    ("POST", "/capture/portfolio"),
    ("POST", "/capture/project"),
    ("POST", "/capture/repo-analysis"),
    ("POST", "/capture/commit-analysis"),
]


@pytest.fixture
def app() -> LocalCompanionApp:
    return LocalCompanionApp(token="local-secret")


@pytest.mark.parametrize(("method", "path"), AUTHENTICATED)
def test_every_non_public_route_requires_a_credential(app, method, path):
    for token in ("", "wrong"):
        status, payload = app.handle(method, path, body=b"{}", token=token)
        assert status == 401, (method, path, token)
        assert payload["ok"] is False


@pytest.mark.parametrize(("method", "path"), AUTHENTICATED)
def test_authenticated_routes_reach_validation_or_a_result(app, method, path):
    status, _ = app.handle(method, path, body=b"{}", token="local-secret")
    # 404 here is a domain lookup ("Captura não encontrada"), not an unknown route
    assert status in {200, 404, 422}, (method, path, status)


def test_public_routes_answer_without_a_credential(app):
    assert app.handle("GET", "/health")[0] == 200
    # pairing still checks the origin; an unknown origin is refused, not asked for a token
    assert app.handle("POST", "/pairing/start", body=b"{}", origin="https://evil.example")[0] == 403


def test_unknown_paths_are_hidden_behind_authentication(app):
    assert app.handle("POST", "/capture/unknown", body=b"{}")[0] == 401
    assert app.handle("POST", "/capture/unknown", body=b"{}", token="local-secret")[0] == 404


def test_a_known_path_with_the_wrong_method_is_405(app):
    status, payload = app.handle("DELETE", "/capture/job", token="local-secret")
    assert status == 405 and payload["ok"] is False


def test_non_local_clients_are_refused_before_anything_else(app):
    assert app.handle("GET", "/health", client_host="10.0.0.5")[0] == 403
