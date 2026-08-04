"""Small persistent SQLite lease and idempotency store for the local scheduler."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database


class SchedulerLeaseStore:
    """Coordinate local scheduler instances without becoming a distributed scheduler."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def acquire(self, lock_name: str, owner_id: str, *, lease_seconds: int = 300) -> bool:
        ensure_database(self.database_path)
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=max(30, min(lease_seconds, 3600)))
        with connect_database(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM scheduler_locks WHERE lock_name = ? AND expires_at <= ?",
                (lock_name, now.isoformat()),
            )
            cursor = connection.execute(
                """INSERT OR IGNORE INTO scheduler_locks
                (lock_name, owner_id, acquired_at, expires_at) VALUES (?, ?, ?, ?)""",
                (lock_name, owner_id, now.isoformat(), expires_at.isoformat()),
            )
        return cursor.rowcount == 1

    def release(self, lock_name: str, owner_id: str) -> None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                "DELETE FROM scheduler_locks WHERE lock_name = ? AND owner_id = ?",
                (lock_name, owner_id),
            )

    def completed(self, operation_key: str) -> bool:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM idempotency_records WHERE operation_key = ?",
                (operation_key,),
            ).fetchone()
        return row is not None

    def mark_completed(self, operation_key: str, result_ref: str) -> None:
        ensure_database(self.database_path)
        now = datetime.now(UTC).isoformat()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT OR IGNORE INTO idempotency_records
                (operation_key, operation_type, result_ref, result_hash, created_at)
                VALUES (?, 'radar_scheduled_run', ?, '', ?)""",
                (operation_key, result_ref, now),
            )


__all__ = ["SchedulerLeaseStore"]
