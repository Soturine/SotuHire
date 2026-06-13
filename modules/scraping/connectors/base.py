"""Base contract for public source connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from modules.scraping.client import ScrapingClient
from modules.scraping.schemas import CollectionResult, ScrapingSource


class PublicSourceConnector(ABC):
    """Collect opportunities from one explicitly configured public source."""

    def __init__(self, client: ScrapingClient | None = None) -> None:
        self.client = client or ScrapingClient()

    @abstractmethod
    def collect(self, source: ScrapingSource) -> CollectionResult:
        """Collect a bounded set of public opportunities."""
