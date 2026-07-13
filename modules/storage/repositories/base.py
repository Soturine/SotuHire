"""Repository contracts shared by local persistence adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, TypeAlias

Entity: TypeAlias = dict[str, object]


class EntityRepository(Protocol):
    """Minimal entity repository used by new storage services."""

    def get(self, entity_id: str) -> Entity | None: ...

    def list(self, *, filters: Mapping[str, object] | None = None) -> list[Entity]: ...

    def save(self, entity: Mapping[str, object]) -> Entity: ...

    def delete(self, entity_id: str) -> bool: ...

    def exists(self, entity_id: str) -> bool: ...
