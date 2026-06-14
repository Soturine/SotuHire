import json

from modules.local_api import LocalCompanionApp
from modules.local_api.server import start_server, stop_server


def test_local_api_rejects_non_local_clients_and_invalid_tokens():
    app = LocalCompanionApp(token="local-secret")

    remote_status, _ = app.handle("GET", "/health", client_host="192.168.1.20")
    token_status, _ = app.handle("GET", "/health", token="wrong")
    ok_status, _ = app.handle("GET", "/health", token="local-secret")

    assert remote_status == 403
    assert token_status == 401
    assert ok_status == 200


def test_local_api_rejects_payload_that_is_too_large():
    app = LocalCompanionApp()
    payload = {
        "url": "https://jobs.example/large",
        "visible_text": "x" * 200_001,
    }

    status, _ = app.handle("POST", "/capture/job", body=json.dumps(payload).encode())

    assert status == 422


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
