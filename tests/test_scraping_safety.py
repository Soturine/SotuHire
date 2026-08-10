import pytest
from modules.scraping.http_safety import UnsafePublicUrl, validate_public_url
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
