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
