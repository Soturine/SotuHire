"""Generic SQLite repository for tables with an id and JSON payload."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from modules.storage.database import connect_database

from .base import Entity

IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


class SqliteRepository:
    """Repository adapter for the simple entity tables in the local database."""

    def __init__(
        self,
        table: str,
        *,
        database_path: str | Path | None = None,
        id_field: str = "id",
    ) -> None:
        if not IDENTIFIER.fullmatch(table) or not IDENTIFIER.fullmatch(id_field):
            raise ValueError("Nome de tabela ou campo inválido.")
        self.table = table
        self.id_field = id_field
        self.database_path = Path(database_path) if database_path is not None else None

    def get(self, entity_id: str) -> Entity | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                f"SELECT payload FROM {self.table} WHERE {self.id_field} = ?",  # noqa: S608
                (entity_id,),
            ).fetchone()
        return _payload(row["payload"]) if row is not None else None

    def list(self, *, filters: Mapping[str, object] | None = None) -> list[Entity]:
        records: list[Entity] = []
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"SELECT payload FROM {self.table} ORDER BY updated_at DESC"  # noqa: S608
            ).fetchall()
        for row in rows:
            item = _payload(row["payload"])
            if not filters or all(item.get(key) == value for key, value in filters.items()):
                records.append(item)
        return records

    def save(self, entity: Mapping[str, object]) -> Entity:
        item = dict(entity)
        entity_id = str(item.get(self.id_field, "")).strip()
        if not entity_id:
            raise ValueError(f"Campo de identidade ausente: {self.id_field}")
        now = datetime.now(UTC).isoformat()
        payload = json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
        with connect_database(self.database_path) as connection:
            connection.execute(
                f"""INSERT INTO {self.table} ({self.id_field}, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT({self.id_field}) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at""",  # noqa: S608
                (entity_id, payload, now, now),
            )
        return item

    def delete(self, entity_id: str) -> bool:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                f"DELETE FROM {self.table} WHERE {self.id_field} = ?",  # noqa: S608
                (entity_id,),
            )
        return cursor.rowcount > 0

    def exists(self, entity_id: str) -> bool:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                f"SELECT 1 FROM {self.table} WHERE {self.id_field} = ?",  # noqa: S608
                (entity_id,),
            ).fetchone()
        return row is not None


def _payload(value: object) -> Entity:
    parsed = json.loads(str(value))
    if not isinstance(parsed, dict):
        raise ValueError("Payload SQLite inválido.")
    return dict(parsed)
