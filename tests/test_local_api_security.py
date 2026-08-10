import json

from modules.local_api import LocalCompanionApp
from modules.local_api.origins import DEFAULT_EXTENSION_ID
from modules.local_api.server import start_server, stop_server


def test_local_api_rejects_non_local_clients_and_invalid_tokens():
    app = LocalCompanionApp(token="local-secret")

    remote_status, _ = app.handle("GET", "/health", client_host="192.168.1.20")
    token_status, _ = app.handle("GET", "/capture/status", token="wrong")
    ok_status, _ = app.handle("GET", "/capture/status", token="local-secret")

    assert remote_status == 403
    assert token_status == 401
    assert ok_status == 200


def test_local_api_rejects_payload_that_is_too_large():
    app = LocalCompanionApp(token="local-secret")
    payload = {
        "url": "https://jobs.example/large",
        "visible_text": "x" * 200_001,
    }

    status, _ = app.handle(
        "POST", "/capture/job", body=json.dumps(payload).encode(), token="local-secret"
    )

    assert status == 422


def test_local_api_extension_pairing_is_one_use_and_origin_bound():
    app = LocalCompanionApp(token="local-secret")
    origin = f"chrome-extension://{DEFAULT_EXTENSION_ID}"
    start_status, start = app.handle("POST", "/pairing/start", body=b"{}", origin=origin)
    complete_body = json.dumps(
        {"challenge_id": start["challenge_id"], "proof": start["proof"]}
    ).encode()
    complete_status, complete = app.handle(
        "POST", "/pairing/complete", body=complete_body, origin=origin
    )
    replay_status, _ = app.handle("POST", "/pairing/complete", body=complete_body, origin=origin)

    assert start_status == 200
    assert complete_status == 200
    assert replay_status == 401
    session_token = str(complete["session_token"])
    assert app.handle("GET", "/capture/status", token=session_token, origin=origin)[0] == 200
    assert (
        app.handle(
            "GET",
            "/capture/status",
            token=session_token,
            origin="chrome-extension://different",
        )[0]
        == 401
    )


def test_local_api_rejects_unlisted_extension_origin() -> None:
    app = LocalCompanionApp(token="local-secret")

    status, _ = app.handle(
        "POST",
        "/pairing/start",
        body=b"{}",
        origin="chrome-extension://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )

    assert status == 403


def test_local_api_server_refuses_public_bind():
    try:
        try:
            start_server(host="0.0.0.0", port=0)
        except ValueError as exc:
            assert "127.0.0.1" in str(exc)
        else:
            raise AssertionError("Public bind should fail")
    finally:
        stop_server()
