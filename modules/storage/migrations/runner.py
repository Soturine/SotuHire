"""Small transactional migration runner with validation history."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from modules.storage.database import (
    connect_database,
    connect_readonly_database,
    default_database_path,
)

from .versions import LATEST_SCHEMA_VERSION, MIGRATIONS


class MigrationError(RuntimeError):
    """Raised when a migration cannot be safely completed."""


class MigrationRunner:
    """Apply ordered migrations in transactions and record their validations."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def current_version(self) -> int:
        if not self.database_path.exists():
            return 0
        with connect_readonly_database(self.database_path) as connection:
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='migration_history'"
            ).fetchone()
            if exists is None:
                return 0
            row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM migration_history WHERE success = 1"
            ).fetchone()
            return int(row[0]) if row is not None else 0

    def apply(self, *, create_backup: bool = True) -> list[int]:
        """Apply all pending migrations and return their version numbers."""
        previous_version = self.current_version()
        pending = [item for item in MIGRATIONS if item.version > previous_version]
        if not pending:
            return []
        if create_backup and previous_version > 0 and self.database_path.exists():
            from modules.storage.backup import backup_database_file

            backup_database_file(self.database_path)
        applied: list[int] = []
        with connect_database(self.database_path) as connection:
            self._bootstrap_history(connection)
            for migration in pending:
                started_at = datetime.now(UTC).isoformat()
                try:
                    migration.up(connection)
                    errors = migration.validation(connection)
                    if errors:
                        raise MigrationError("; ".join(errors))
                    connection.execute(
                        """INSERT OR REPLACE INTO migration_history
                        (version, description, applied_at, success, validation_errors,
                         rollback_strategy, created_at)
                        VALUES (?, ?, ?, 1, '[]', ?, ?)""",
                        (
                            migration.version,
                            migration.description,
                            started_at,
                            migration.rollback_strategy,
                            migration.created_at,
                        ),
                    )
                    connection.commit()
                    applied.append(migration.version)
                except Exception as exc:
                    connection.rollback()
                    raise MigrationError(
                        f"Migração {migration.version} falhou: {type(exc).__name__}: {exc}"
                    ) from exc
        return applied

    def verify(self) -> list[str]:
        """Validate schema version, migration records, tables and foreign keys."""
        if not self.database_path.exists():
            return [f"Banco ausente: {self.database_path}"]
        errors: list[str] = []
        with connect_readonly_database(self.database_path) as connection:
            history_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='migration_history'"
            ).fetchone()
            if history_exists is None:
                return ["Tabela ausente: migration_history"]
            metadata_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_metadata'"
            ).fetchone()
            if metadata_exists is None:
                return ["Tabela ausente: schema_metadata"]
            history_row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM migration_history WHERE success = 1"
            ).fetchone()
            history_version = int(history_row[0]) if history_row is not None else 0
            if history_version != LATEST_SCHEMA_VERSION:
                errors.append(f"Schema atual {history_version}; esperado {LATEST_SCHEMA_VERSION}")
            metadata_row = connection.execute(
                "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
            ).fetchone()
            try:
                metadata_version = int(metadata_row[0]) if metadata_row is not None else -1
            except (TypeError, ValueError):
                metadata_version = -1
            if metadata_version != history_version:
                errors.append(
                    "Schema divergente entre schema_metadata "
                    f"({metadata_version}) e migration_history ({history_version})"
                )
            for migration in MIGRATIONS:
                row = connection.execute(
                    "SELECT success FROM migration_history WHERE version = ?",
                    (migration.version,),
                ).fetchone()
                if row is None or not bool(row[0]):
                    errors.append(f"Migração não aplicada: {migration.version}")
                errors.extend(migration.validation(connection))
            foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
            errors.extend(f"Foreign key inválida: {tuple(row)}" for row in foreign_key_errors)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if integrity is None or str(integrity[0]).casefold() != "ok":
                errors.append(
                    f"Integrity check falhou: {integrity[0] if integrity else 'sem retorno'}"
                )
        return list(dict.fromkeys(errors))

    @staticmethod
    def _bootstrap_history(connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS migration_history (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                success INTEGER NOT NULL,
                validation_errors TEXT NOT NULL DEFAULT '[]',
                rollback_strategy TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        connection.commit()


def ensure_database(path: str | Path | None = None) -> Path:
    """Create or migrate the local database and return its path."""
    runner = MigrationRunner(path)
    runner.apply()
    errors = runner.verify()
    if errors:
        raise MigrationError("; ".join(errors))
    return runner.database_path


__all__ = ["LATEST_SCHEMA_VERSION", "MigrationError", "MigrationRunner", "ensure_database"]
