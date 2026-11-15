"""Small transactional migration runner with validation history."""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
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


# Files already migrated and verified in this process. SH-NEW-001: every repository method called
# ensure_database(), which runs full integrity and foreign-key checks (~12 ms on a 1.7 MB
# database), several times per operation. The full check is skipped only while all of these hold:
#
# * the file's fingerprint is unchanged: size and mtime of the database, a hash of its 100-byte
#   header (page size, schema cookie, change counters), the WAL's size and its 32-byte header. The
#   WAL header carries salts SQLite changes every time the WAL restarts after a checkpoint, so a
#   rewrite of WAL frames that does not grow the file still changes the fingerprint. The WAL's
#   mtime is left out: SQLite touches it on every WAL-mode connection, even to read;
# * the last full check is younger than VERIFY_MAX_AGE_S. Damage that preserves size, mtime and
#   both headers (bit rot, a tool that restores timestamps) is therefore caught within that
#   window, and at the next process start (the cache lives in memory only);
# * nothing invalidated it: restoring a backup calls forget_verified_databases().
#
# Migrations are never skipped by this cache: any schema change rewrites the database header
# (schema cookie), and a schema change made outside this function is an error either way.
VERIFY_MAX_AGE_S = 600.0
_VERIFIED: dict[str, tuple[tuple, float]] = {}
_VERIFIED_LOCK = threading.Lock()


def _read_prefix(path: Path, size: int) -> bytes:
    try:
        with path.open("rb") as handle:
            return handle.read(size)
    except FileNotFoundError:
        return b""


def _fingerprint(database: Path) -> tuple:
    try:
        stat = database.stat()
        main = (stat.st_size, stat.st_mtime_ns)
    except FileNotFoundError:
        main = (-1, -1)
    header = hashlib.sha256(_read_prefix(database, 100)).hexdigest()
    wal_path = database.with_name(database.name + "-wal")
    try:
        wal_size = wal_path.stat().st_size
    except FileNotFoundError:
        wal_size = 0  # SQLite deletes an empty WAL when the last connection closes: same state
    wal_header = _read_prefix(wal_path, 32) if wal_size else b""
    return (*main, header, wal_size, wal_header)


def ensure_database(path: str | Path | None = None) -> Path:
    """Create or migrate the local database and return its path.

    Migration and the full integrity check are skipped only for a file this process verified with
    the same fingerprint less than VERIFY_MAX_AGE_S ago (see ``_VERIFIED``).
    """
    runner = MigrationRunner(path)
    database = runner.database_path
    key = str(Path(database).resolve())
    with _VERIFIED_LOCK:
        cached = _VERIFIED.get(key)
        if (
            cached is not None
            and database.is_file()
            and cached[0] == _fingerprint(database)
            and time.monotonic() - cached[1] < VERIFY_MAX_AGE_S
        ):
            return database
        _VERIFIED.pop(key, None)  # until this check passes, the file is not verified
    runner.apply()
    errors = runner.verify()
    if errors:
        raise MigrationError("; ".join(errors))
    with _VERIFIED_LOCK:
        _VERIFIED[key] = (_fingerprint(database), time.monotonic())
    return database


def forget_verified_databases() -> None:
    """Drop the verification cache: after a restore, or when files were replaced by other means."""
    with _VERIFIED_LOCK:
        _VERIFIED.clear()


__all__ = [
    "LATEST_SCHEMA_VERSION",
    "MigrationError",
    "MigrationRunner",
    "ensure_database",
    "forget_verified_databases",
]
