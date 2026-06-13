"""Small per-domain rate limiter."""

from __future__ import annotations

import time
from collections.abc import Callable
from urllib.parse import urlparse


class DomainRateLimiter:
    """Wait between requests to the same public domain."""

    def __init__(
        self,
        default_delay_seconds: float = 2.0,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.default_delay_seconds = default_delay_seconds
        self.clock = clock
        self.sleeper = sleeper
        self._last_request: dict[str, float] = {}

    def wait(self, url: str, delay_seconds: float | None = None) -> float:
        """Wait as needed and return the applied delay."""
        domain = urlparse(url).netloc.lower()
        delay = delay_seconds if delay_seconds is not None else self.default_delay_seconds
        previous = self._last_request.get(domain)
        now = self.clock()
        remaining = max(0.0, delay - (now - previous)) if previous is not None else 0.0
        if remaining:
            self.sleeper(remaining)
        self._last_request[domain] = self.clock()
        return remaining
