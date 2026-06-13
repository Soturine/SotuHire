"""Base contract for public source connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from modules.scraping.client import ScrapingClient
from modules.scraping.schemas import CollectionResult, FetchResult, ScrapingSource


class FetchClient(Protocol):
    """Small fetch contract used by connectors and fixture clients."""

    def fetch(self, url: str, *, delay_seconds: float = 2.0) -> FetchResult: ...


class PublicSourceConnector(ABC):
    """Collect opportunities from one explicitly configured public source."""

    def __init__(self, client: FetchClient | None = None) -> None:
        self.client = client or ScrapingClient()

    @abstractmethod
    def collect(self, source: ScrapingSource) -> CollectionResult:
        """Collect a bounded set of public opportunities."""
