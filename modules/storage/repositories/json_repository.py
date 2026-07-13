"""Compatibility repositories for existing JSON and JSONL stores."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

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
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"O store JSON deve conter uma lista: {self.path}")
        return [dict(item) for item in payload if isinstance(item, dict)]

    def _write(self, records: list[Entity]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(records, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        temporary.replace(self.path)


class JsonlRepository(JsonRepository):
    """Atomic line-delimited JSON repository used by legacy stores."""

    def _read(self) -> list[Entity]:
        if not self.path.exists():
            return []
        records: list[Entity] = []
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"Linha JSONL inválida em {self.path}:{line_number}")
            records.append(dict(payload))
        return records

    def _write(self, records: list[Entity]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        content = "\n".join(json.dumps(item, ensure_ascii=False, default=str) for item in records)
        temporary.write_text(content + ("\n" if content else ""), encoding="utf-8")
        temporary.replace(self.path)
