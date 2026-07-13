"""SQLite connection helpers for the local-first SotuHire data layer."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Literal

DEFAULT_DATABASE_NAME = "sotuhire.db"


class SotuHireConnection(sqlite3.Connection):
    """Connection that closes after a ``with`` block, including on rollback."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        try:
            super().__exit__(exc_type, exc_value, traceback)
            return False
        finally:
            self.close()


def default_data_dir() -> Path:
    """Return the configured local data directory."""
    return Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))


def default_database_path() -> Path:
    """Return the default SQLite database path."""
    return default_data_dir() / DEFAULT_DATABASE_NAME


def connect_database(path: str | Path | None = None) -> sqlite3.Connection:
    """Open a configured SQLite connection with local reliability safeguards."""
    database_path = Path(path) if path is not None else default_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        database_path,
        timeout=5.0,
        factory=SotuHireConnection,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection


def connect_readonly_database(path: str | Path) -> sqlite3.Connection:
    """Open an existing SQLite database without changing schema or journal settings."""
    database_path = Path(path).resolve()
    if not database_path.is_file():
        raise FileNotFoundError(database_path)
    connection = sqlite3.connect(
        f"file:{database_path.as_posix()}?mode=ro",
        uri=True,
        timeout=5.0,
        factory=SotuHireConnection,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def database_path_for(connection: sqlite3.Connection) -> Path | None:
    """Return the main database path for a connection when it is file-backed."""
    row = connection.execute("PRAGMA database_list").fetchone()
    if row is None or not row[2]:
        return None
    return Path(str(row[2]))
