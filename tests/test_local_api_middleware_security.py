from __future__ import annotations

import pytest
from apps.api.config import ApiSettings
from apps.api.main import create_app
from fastapi.testclient import TestClient
from modules.security import LocalAuthManager, PairingError, RequestLimitError, RequestPolicy

TOKEN = "middleware-test-token-with-more-than-thirty-two-characters"
ORIGIN = "http://127.0.0.1:5173"


def _client(**settings_overrides) -> TestClient:
    settings = ApiSettings(installation_token=TOKEN, **settings_overrides)
    return TestClient(create_app(settings), base_url="http://127.0.0.1:8787")


def test_health_is_public_and_does_not_serialize_authentication_material() -> None:
    response = _client().get("/api/v1/health")

    assert response.status_code == 200
    serialized = response.text
    assert TOKEN not in serialized
    assert "installation_token" not in serialized
    assert "local-auth" not in serialized


def test_unknown_origin_invalid_host_and_missing_token_are_rejected() -> None:
    client = _client()

    bad_origin = client.get("/api/v1/profile", headers={"Origin": "https://attacker.example"})
    bad_host = client.get(
        "/api/v1/profile",
        headers={"Host": "attacker.example", "X-SotuHire-Token": TOKEN},
    )
    missing_token = client.get("/api/v1/profile")

    assert bad_origin.status_code == 403
    assert bad_origin.json()["error"]["code"] == "origin_not_allowed"
    assert bad_host.status_code == 400
    assert missing_token.status_code == 401


def test_native_client_without_origin_works_only_with_valid_token() -> None:
    client = _client()

    accepted = client.get("/api/v1/profile", headers={"X-SotuHire-Token": TOKEN})
    rejected = client.get("/api/v1/profile", headers={"X-SotuHire-Token": "invalid"})

    assert accepted.status_code == 200
    assert rejected.status_code == 401


def test_web_pairing_sets_httponly_cookie_requires_csrf_and_rejects_replay() -> None:
    client = _client()
    start = client.post(
        "/api/v1/security/pairing/start",
        headers={"Origin": ORIGIN},
        json={"client_kind": "web", "client_name": "Teste"},
    )
    challenge = start.json()["data"]
    complete = client.post(
        "/api/v1/security/pairing/complete",
        headers={"Origin": ORIGIN},
        json={
            "challenge_id": challenge["challenge_id"],
            "proof": challenge["proof"],
            "client_kind": "web",
        },
    )
    csrf = complete.json()["data"]["csrf_token"]

    assert start.status_code == 200
    assert complete.status_code == 200
    assert "HttpOnly" in complete.headers["set-cookie"]
    assert "SameSite=strict" in complete.headers["set-cookie"]
    assert client.get("/api/v1/profile", headers={"Origin": ORIGIN}).status_code == 200
    assert (
        client.post("/api/v1/profile/deduplicate", headers={"Origin": ORIGIN}, json={}).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/profile/deduplicate",
            headers={"Origin": ORIGIN, "X-SotuHire-CSRF": csrf},
            json={},
        ).status_code
        != 401
    )
    replay = client.post(
        "/api/v1/security/pairing/complete",
        headers={"Origin": ORIGIN},
        json={
            "challenge_id": challenge["challenge_id"],
            "proof": challenge["proof"],
            "client_kind": "web",
        },
    )
    assert replay.status_code == 401


def test_pairing_expiry_is_enforced_without_exposing_proof() -> None:
    now = [100.0]
    manager = LocalAuthManager(
        installation_token=TOKEN,
        pairing_ttl_seconds=10,
        clock=lambda: now[0],
    )
    challenge = manager.start_pairing(origin=ORIGIN, client_kind="web")
    now[0] = 111.0

    try:
        manager.complete_pairing(
            challenge_id=challenge.challenge_id,
            proof=challenge.proof,
            origin=ORIGIN,
            client_kind="web",
        )
    except PairingError as exc:
        assert challenge.proof not in str(exc)
    else:
        raise AssertionError("Pairing expirado deveria ser rejeitado")


def test_body_content_type_batch_and_depth_limits_are_enforced() -> None:
    client = _client(max_body_bytes=128, max_batch_items=2, max_json_depth=3)
    headers = {"X-SotuHire-Token": TOKEN}

    too_large = client.post(
        "/api/v1/profile/import-text", headers=headers, json={"text": "x" * 256}
    )
    wrong_type = client.post(
        "/api/v1/profile/import-text",
        headers={**headers, "Content-Type": "text/plain"},
        content="plain",
    )
    batch = client.post("/api/v1/profile/import-text", headers=headers, json={"items": [1, 2, 3]})
    deep = client.post("/api/v1/profile/import-text", headers=headers, json={"a": {"b": {"c": 1}}})

    assert too_large.status_code == 413
    assert wrong_type.status_code == 415
    assert batch.status_code == 422
    assert batch.json()["error"]["code"] == "batch_too_large"
    assert deep.status_code == 422
    assert deep.json()["error"]["code"] == "json_too_deep"


def test_request_policy_rejects_invalid_content_length() -> None:
    try:
        RequestPolicy().validate_content_length("not-a-number")
    except RequestLimitError as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("Content-Length inválido deveria ser rejeitado")


def test_preflight_is_allowed_only_for_configured_origin() -> None:
    client = _client()
    accepted = client.options(
        "/api/v1/profile",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    rejected = client.options(
        "/api/v1/profile",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert accepted.status_code == 200
    assert accepted.headers["access-control-allow-origin"] == ORIGIN
    assert rejected.status_code == 403


def test_environment_rejects_public_bind_and_remote_origin_without_opt_in(monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_API_HOST", "0.0.0.0")
    with pytest.raises(ValueError, match="loopback"):
        ApiSettings.from_env()

    monkeypatch.setenv("SOTUHIRE_API_HOST", "127.0.0.1")
    monkeypatch.setenv("SOTUHIRE_API_ALLOWED_ORIGINS", "https://public.example")
    with pytest.raises(ValueError, match="ALLOW_REMOTE_ORIGINS"):
        ApiSettings.from_env()
