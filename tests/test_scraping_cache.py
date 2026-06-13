from pathlib import Path

from modules.scraping.cache import ScrapingCache
from modules.scraping.client import ScrapingClient
from modules.scraping.schemas import FetchResult


def test_cache_avoids_repeated_download(tmp_path: Path):
    calls = []

    def transport(url, headers, timeout, max_bytes):
        calls.append(url)
        return FetchResult(url=url, status_code=200, text="public")

    client = ScrapingClient(
        transport=transport,
        robot_checker=lambda url, agent: True,
        cache=ScrapingCache(tmp_path),
    )
    client.fetch("https://example.com/jobs", delay_seconds=0.2)
    cached = client.fetch("https://example.com/jobs", delay_seconds=0.2)

    assert len(calls) == 1
    assert cached.from_cache
