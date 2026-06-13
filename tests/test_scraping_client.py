from pathlib import Path

from modules.scraping.cache import ScrapingCache
from modules.scraping.client import ScrapingClient
from modules.scraping.schemas import FetchResult


def test_client_uses_identifiable_agent_and_public_transport(tmp_path: Path):
    captured = {}

    def transport(url, headers, timeout, max_bytes):
        captured.update(url=url, headers=headers, timeout=timeout, max_bytes=max_bytes)
        return FetchResult(url=url, status_code=200, text="ok")

    client = ScrapingClient(
        transport=transport,
        robot_checker=lambda url, agent: True,
        cache=ScrapingCache(tmp_path),
    )
    result = client.fetch("https://example.com/jobs", delay_seconds=0.2)

    assert result.text == "ok"
    assert captured["headers"]["User-Agent"].startswith("SotuHire/")
