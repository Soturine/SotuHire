"""Local cache for bounded public fetches."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from modules.scraping.schemas import FetchResult


class ScrapingCache:
    """Persist public responses locally and expire them after a configurable TTL."""

    def __init__(
        self,
        directory: str | Path = "data/scraping-cache",
        ttl: timedelta = timedelta(hours=6),
    ) -> None:
        self.directory = Path(directory)
        self.ttl = ttl

    def _path(self, url: str) -> Path:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.directory / f"{key}.json"

    def get(self, url: str) -> FetchResult | None:
        target = self._path(url)
        if not target.exists():
            return None
        try:
            result = FetchResult.model_validate_json(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if datetime.now(UTC) - result.collected_at > self.ttl:
            return None
        return result.model_copy(update={"from_cache": True})

    def set(self, result: FetchResult) -> FetchResult:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self._path(result.url)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(result.model_dump(mode="json"), ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(target)
        return result
