"""Identifiable HTTP client for public pages."""

from __future__ import annotations

import logging
from collections.abc import Callable
from urllib.request import Request, urlopen

from modules.scraping.rate_limit import DomainRateLimiter
from modules.scraping.robots import inspect_source_safety, robots_allows
from modules.scraping.schemas import FetchResult

LOGGER = logging.getLogger("sotuhire.scraping")
USER_AGENT = "SotuHire/0.7 (+responsible-public-opportunity-collection)"


class ScrapingClient:
    """Fetch public content with safety checks, rate limiting, and bounded reads."""

    def __init__(
        self,
        *,
        user_agent: str = USER_AGENT,
        timeout_seconds: float = 15,
        max_bytes: int = 2_000_000,
        rate_limiter: DomainRateLimiter | None = None,
        robot_checker: Callable[[str, str], bool] = robots_allows,
        transport: Callable[[str, dict[str, str], float, int], FetchResult] | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes
        self.rate_limiter = rate_limiter or DomainRateLimiter()
        self.robot_checker = robot_checker
        self.transport = transport or self._urllib_transport

    def fetch(self, url: str, *, delay_seconds: float = 2.0) -> FetchResult:
        """Fetch one public URL or raise a clear safety error."""
        safety = inspect_source_safety(url)
        if not safety.allowed:
            raise ValueError(safety.warning)
        if not self.robot_checker(url, self.user_agent):
            raise PermissionError("robots.txt não permite coleta desta URL.")
        self.rate_limiter.wait(url, delay_seconds)
        LOGGER.info("Collecting public URL domain=%s type=%s", safety.domain, safety.detected_type)
        return self.transport(
            url,
            {"User-Agent": self.user_agent, "Accept": "text/html, application/xml, text/xml"},
            self.timeout_seconds,
            self.max_bytes,
        )

    @staticmethod
    def _urllib_transport(
        url: str,
        headers: dict[str, str],
        timeout_seconds: float,
        max_bytes: int,
    ) -> FetchResult:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError("Resposta excede o limite seguro de coleta.")
            content_type = response.headers.get("Content-Type", "")
            encoding = response.headers.get_content_charset() or "utf-8"
            return FetchResult(
                url=response.geturl(),
                status_code=response.status,
                content_type=content_type,
                text=payload.decode(encoding, errors="replace"),
            )
