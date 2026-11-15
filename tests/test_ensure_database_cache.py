"""SH-NEW-001: ensure_database() verifies a file once per content, not once per repository call."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest
from modules.storage.migrations import MigrationError, forget_verified_databases
from modules.storage.migrations import runner as runner_module
from modules.storage.migrations.runner import MigrationRunner, ensure_database


@pytest.fixture(autouse=True)
def _fresh_cache():
    forget_verified_databases()
    yield
    forget_verified_databases()


def _count_verify(monkeypatch) -> list[int]:
    calls: list[int] = []
    original = MigrationRunner.verify

    def counting(self):
        calls.append(1)
        return original(self)

    monkeypatch.setattr(MigrationRunner, "verify", counting)
    return calls


def test_repeated_calls_on_unchanged_file_verify_once(tmp_path: Path, monkeypatch) -> None:
    calls = _count_verify(monkeypatch)
    database = tmp_path / "sotuhire.db"
    for _ in range(5):
        ensure_database(database)
    assert len(calls) == 1


def test_reads_through_the_app_connection_do_not_force_a_new_check(
    tmp_path: Path, monkeypatch
) -> None:
    """The first cache keyed on the WAL's mtime never hit: SQLite touches the -wal file whenever a
    WAL-mode connection opens, even to read (found by measuring list_nodes after the change)."""
    from modules.storage.database import connect_database

    calls = _count_verify(monkeypatch)
    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    for _ in range(3):
        with connect_database(database) as connection:
            connection.execute("SELECT 1").fetchone()
        ensure_database(database)
    assert len(calls) == 1


def test_a_write_makes_the_next_call_verify_again(tmp_path: Path, monkeypatch) -> None:
    calls = _count_verify(monkeypatch)
    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS probe (x INTEGER)")
        connection.execute("INSERT INTO probe VALUES (1)")
    ensure_database(database)
    assert len(calls) == 2


def test_a_replaced_corrupt_file_is_still_rejected(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    good = tmp_path / "good.db"
    shutil.copy2(database, good)
    data = bytearray(database.read_bytes())
    data[100:4096] = b"\x00" * (4096 - 100)  # wreck the header area: no longer a valid database
    database.write_bytes(bytes(data))
    with pytest.raises((MigrationError, sqlite3.DatabaseError)):
        ensure_database(database)
    assert runner_module._VERIFIED.get(str(database.resolve())) is None
