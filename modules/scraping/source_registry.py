"""Extensible registry of public source connectors."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

ConnectorFactory = Callable[..., Any]


class SourceRegistry:
    """Map configured source types to connector factories."""

    def __init__(self) -> None:
        self._factories: dict[str, ConnectorFactory] = {}

    def register(self, source_type: str, factory: ConnectorFactory) -> None:
        self._factories[source_type] = factory

    def create(self, source_type: str, **kwargs: object) -> Any:
        if source_type not in self._factories:
            raise KeyError(f"Tipo de fonte não registrado: {source_type}")
        return self._factories[source_type](**kwargs)

    def available_types(self) -> list[str]:
        return sorted(self._factories)


def default_source_registry() -> SourceRegistry:
    """Return the built-in connector registry."""
    from modules.scraping.connectors.authenticated_browser import AuthenticatedBrowserConnector
    from modules.scraping.connectors.company_career_page import CompanyCareerPageConnector
    from modules.scraping.connectors.generic_public_page import GenericPublicPageConnector
    from modules.scraping.connectors.manual_url import ManualUrlConnector
    from modules.scraping.connectors.rss_feed import RssFeedConnector

    registry = SourceRegistry()
    registry.register("authenticated_browser", AuthenticatedBrowserConnector)
    registry.register("manual_url", ManualUrlConnector)
    registry.register("generic_public_page", GenericPublicPageConnector)
    registry.register("company_career_page", CompanyCareerPageConnector)
    registry.register("rss", RssFeedConnector)
    return registry
