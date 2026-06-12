"""Connector registry."""

from __future__ import annotations

from modules.sources.base import JobSourceConnector

_CONNECTORS: dict[str, JobSourceConnector] = {}


def register_connector(connector: JobSourceConnector) -> None:
    """Register a connector instance."""
    _CONNECTORS[connector.source_name] = connector


def get_connector(name: str) -> JobSourceConnector | None:
    """Get connector by name."""
    return _CONNECTORS.get(name)


def list_connectors() -> list[str]:
    """List connector names."""
    return sorted(_CONNECTORS)
