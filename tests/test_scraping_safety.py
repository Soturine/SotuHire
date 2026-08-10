from email.message import Message

import pytest
from modules.scraping.browser_inputs import validate_browser_start_url, validate_local_cdp_url
from modules.scraping.http_safety import (
    PublicHttpResponse,
    UnsafePublicUrl,
    request_public_url,
    resolve_public_url,
    validate_public_url,
)
from modules.scraping.robots import inspect_source_safety


def test_linkedin_public_mode_routes_to_authenticated_browser():
    safety = inspect_source_safety("https://www.linkedin.com/jobs/")

    assert not safety.allowed
    assert safety.robots_status == "bloqueado"
    assert "Navegador autenticado autorizado" in safety.warning


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/jobs",
        "http://[::1]/jobs",
        "http://10.0.0.8/jobs",
        "https://user:secret@example.com/jobs",
        "https://example.com:8443/jobs",
        "file:///etc/passwd",
    ],
)
def test_public_source_safety_blocks_ssrf_targets(url: str) -> None:
    assert not inspect_source_safety(url).allowed


def test_dns_resolution_rejects_private_answers_and_accepts_only_global_answers() -> None:
    with pytest.raises(UnsafePublicUrl, match="locais ou privados"):
        validate_public_url(
            "https://jobs.example/jobs",
            resolve=True,
            resolver=lambda _host, _port: ["203.0.113.10", "10.0.0.5"],
        )

    parsed = validate_public_url(
        "https://jobs.example/jobs",
        resolve=True,
        resolver=lambda _host, _port: ["8.8.8.8", "2606:4700:4700::1111"],
    )
    assert parsed.hostname == "jobs.example"


@pytest.mark.parametrize(
    "url",
    [
        "--disable-web-security",
        "file:///etc/passwd",
        "https://user:secret@example.com/jobs",
        "https://example.com\r\n--remote-debugging-port=1",
    ],
)
def test_browser_start_url_cannot_become_a_chromium_option(url: str) -> None:
    with pytest.raises(ValueError):
        validate_browser_start_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com:9222",
        "http://127.0.0.1:9223",
        "https://127.0.0.1:9222",
        "http://127.0.0.1:9222/json",
        "--remote-debugging-port=1",
    ],
)
def test_cdp_boundary_accepts_only_the_fixed_loopback_endpoint(url: str) -> None:
    with pytest.raises(ValueError):
        validate_local_cdp_url(url)
    assert validate_local_cdp_url("http://127.0.0.1:9222") == "http://127.0.0.1:9222"


def test_resolved_public_target_retains_only_validated_addresses() -> None:
    target = resolve_public_url(
        "https://jobs.example./roles",
        resolver=lambda host, port: ["8.8.8.8"],
    )
    assert target.hostname == "jobs.example"
    assert target.port == 443
    assert target.addresses == ("8.8.8.8",)


def test_public_redirect_is_revalidated_before_second_connection(monkeypatch) -> None:
    calls = []

    def fake_request(target, headers, *, timeout, max_bytes, method, body):
        calls.append(target.hostname)
        message = Message()
        message["Location"] = "http://127.0.0.1/admin"
        return PublicHttpResponse(url=target.url, status=302, headers=message, body=b"")

    monkeypatch.setattr("modules.scraping.http_safety._request_pinned", fake_request)
    with pytest.raises(UnsafePublicUrl, match="locais ou privados"):
        request_public_url(
            "https://jobs.example/roles",
            resolver=lambda host, port: ["8.8.8.8"],
        )
    assert calls == ["jobs.example"]


@pytest.mark.parametrize("url", ["http://example.com:443/x", "https://example.com:80/x"])
def test_mixed_protocol_port_is_rejected(url: str) -> None:
    with pytest.raises(UnsafePublicUrl, match="corresponder"):
        validate_public_url(url)
