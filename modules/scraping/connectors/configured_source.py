"""Load and collect explicitly configured public sources."""

from __future__ import annotations

import tomllib
from pathlib import Path

from modules.scraping.connectors.base import FetchClient, PublicSourceConnector
from modules.scraping.schemas import CollectionResult, ScrapingSource
from modules.scraping.source_registry import SourceRegistry


def load_configured_sources(path: str | Path = "config/sources.toml") -> list[ScrapingSource]:
    """Load validated sources from a local TOML file."""
    target = Path(path)
    if not target.exists():
        return []
    with target.open("rb") as file:
        payload = tomllib.load(file)
    return [ScrapingSource.model_validate(item) for item in payload.get("sources", [])]


class ConfiguredSourceConnector(PublicSourceConnector):
    """Dispatch a configured source through the connector registry."""

    def __init__(self, registry: SourceRegistry, client: FetchClient | None = None) -> None:
        super().__init__(client=client)
        self.registry = registry

    def collect(self, source: ScrapingSource) -> CollectionResult:
        connector = self.registry.create(source.type, client=self.client)
        return connector.collect(source)
