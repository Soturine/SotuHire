"""Compatibility repositories for existing JSON and JSONL stores."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from modules.storage.json_recovery import (
    atomic_write_json,
    atomic_write_jsonl,
    load_json,
    load_jsonl,
)

from .base import Entity


class JsonRepository:
    """Atomic list-based JSON repository used during gradual migration."""

    def __init__(self, path: str | Path, *, id_field: str = "id") -> None:
        self.path = Path(path)
        self.id_field = id_field

    def get(self, entity_id: str) -> Entity | None:
        return next(
            (item for item in self.list() if str(item.get(self.id_field, "")) == entity_id),
            None,
        )

    def list(self, *, filters: Mapping[str, object] | None = None) -> list[Entity]:
        records = self._read()
        if not filters:
            return records
        return [
            item
            for item in records
            if all(item.get(key) == value for key, value in filters.items())
        ]

    def save(self, entity: Mapping[str, object]) -> Entity:
        item = dict(entity)
        entity_id = str(item.get(self.id_field, "")).strip()
        if not entity_id:
            raise ValueError(f"Campo de identidade ausente: {self.id_field}")
        records = self._read()
        for index, current in enumerate(records):
            if str(current.get(self.id_field, "")) == entity_id:
                records[index] = item
                break
        else:
            records.append(item)
        self._write(records)
        return item

    def delete(self, entity_id: str) -> bool:
        records = self._read()
        remaining = [item for item in records if str(item.get(self.id_field, "")) != entity_id]
        if len(remaining) == len(records):
            return False
        self._write(remaining)
        return True

    def exists(self, entity_id: str) -> bool:
        return self.get(entity_id) is not None

    def _read(self) -> list[Entity]:
        payload = load_json(self.path, validator=_entity_list, default_factory=list)
        return [dict(item) for item in payload if isinstance(item, dict)]

    def _write(self, records: list[Entity]) -> None:
        atomic_write_json(self.path, records)


class JsonlRepository(JsonRepository):
    """Atomic line-delimited JSON repository used by legacy stores."""

    def _read(self) -> list[Entity]:
        return load_jsonl(self.path, validator=_entity)

    def _write(self, records: list[Entity]) -> None:
        atomic_write_jsonl(self.path, records)


def _entity(payload: object) -> Entity:
    if not isinstance(payload, dict):
        raise ValueError("Registro JSONL deve ser um objeto.")
    return dict(payload)


def _entity_list(payload: object) -> list[object]:
    if not isinstance(payload, list):
        raise ValueError("Store JSON deve conter uma lista.")
    return payload
