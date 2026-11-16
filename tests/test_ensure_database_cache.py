"""SH-NEW-001: ensure_database() verifies a file once per content, within a bounded age.

The cache must never hide a change it can see: a write (growing or not), a WAL restart that reuses
frames without growing the file, concurrent writers, a restore. What it cannot see by itself
(damage that preserves size, mtime and both headers) is caught when the verification expires.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import threading
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


def _wal_connection(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database, isolation_level=None)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("CREATE TABLE IF NOT EXISTS probe (value TEXT)")
    return connection


def test_repeated_calls_on_unchanged_file_verify_once(tmp_path: Path, monkeypatch) -> None:
    calls = _count_verify(monkeypatch)
    database = tmp_path / "sotuhire.db"
    for _ in range(5):
        ensure_database(database)
    assert len(calls) == 1


def test_reads_through_the_app_connection_do_not_force_a_new_check(
    tmp_path: Path, monkeypatch
) -> None:
    """SQLite touches the -wal file whenever a WAL-mode connection opens, even to read."""
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


def test_a_wal_restart_that_reuses_frames_without_growing_is_seen(
    tmp_path: Path, monkeypatch
) -> None:
    """After a checkpoint the next write restarts the WAL from its first frame: the file keeps its
    size and the main database is not touched. Only the WAL header (new salts) changes."""
    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    keeper = _wal_connection(database)  # keeps the WAL file from being deleted between steps
    try:
        keeper.execute("INSERT INTO probe VALUES (?)", ("a" * 64,))
        keeper.execute("PRAGMA wal_checkpoint(PASSIVE)")
        calls = _count_verify(monkeypatch)
        ensure_database(database)
        wal = database.with_name(database.name + "-wal")
        size_before, main_before = wal.stat().st_size, database.stat().st_mtime_ns
        keeper.execute("INSERT INTO probe VALUES (?)", ("b" * 64,))
        assert wal.stat().st_size == size_before  # no growth: frames were rewritten in place
        assert database.stat().st_mtime_ns == main_before  # main file untouched
        ensure_database(database)
    finally:
        keeper.close()
    assert len(calls) == 2


def test_concurrent_writers_never_leave_a_stale_verification(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    _wal_connection(database).close()
    errors: list[BaseException] = []

    def writer(index: int) -> None:
        try:
            for step in range(15):
                with sqlite3.connect(database, timeout=10) as connection:
                    connection.execute("INSERT INTO probe VALUES (?)", (f"{index}-{step}",))
                ensure_database(database)
        except BaseException as exc:  # noqa: BLE001 - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(index,)) for index in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    key = str(database.resolve())
    # whatever the interleaving, the cached fingerprint is the file as it is now, or nothing
    cached = runner_module._VERIFIED.get(key)
    assert cached is None or cached[0] == runner_module._fingerprint(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM probe").fetchone()[0] == 60


def test_restoring_a_backup_drops_the_verification(tmp_path: Path, monkeypatch) -> None:
    from modules.storage.backup import create_backup, restore_backup

    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    archive = create_backup(data_dir=tmp_path).archive_path
    ensure_database(database)
    assert str(database.resolve()) in runner_module._VERIFIED
    restore_backup(archive, destination=tmp_path, dry_run=False)
    assert runner_module._VERIFIED == {}
    calls = _count_verify(monkeypatch)
    ensure_database(database)
    assert len(calls) == 1


def test_damage_that_keeps_size_and_mtime_is_caught_when_the_verification_expires(
    tmp_path: Path, monkeypatch
) -> None:
    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    with sqlite3.connect(database) as connection:  # make the file span several pages
        connection.execute("CREATE TABLE filler (x TEXT)")
        connection.executemany("INSERT INTO filler VALUES (?)", [("z" * 500,)] * 200)
        connection.commit()  # a checkpoint inside the open transaction is refused
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    ensure_database(database)
    stat = database.stat()
    data = bytearray(database.read_bytes())
    data[4096:8192] = b"\xff" * 4096  # wreck the second page, keep the header
    database.write_bytes(bytes(data))
    os.utime(database, ns=(stat.st_atime_ns, stat.st_mtime_ns))  # a tool that keeps timestamps

    ensure_database(database)  # within the window the cache cannot see this: documented bound

    monkeypatch.setattr(runner_module, "VERIFY_MAX_AGE_S", 0.0)
    with pytest.raises((MigrationError, sqlite3.DatabaseError)):
        ensure_database(database)


def test_a_verification_is_trusted_for_less_than_its_maximum_age_exactly(
    tmp_path: Path, monkeypatch
) -> None:
    """Found by Assertiva mutation (2026-11-15): with the age forced to 0, `-` replaced by `/`, `//`
    or `%`, and `<` by `<=`, all survived. A controlled clock pins the boundary."""
    database = tmp_path / "sotuhire.db"
    now = [100.0]
    monkeypatch.setattr(runner_module.time, "monotonic", lambda: now[0])
    ensure_database(database)  # verified at t=100
    calls = _count_verify(monkeypatch)
    now[0] = 100.0 + 599.0
    ensure_database(database)
    assert len(calls) == 0  # still trusted one second before the limit
    now[0] = 100.0 + runner_module.VERIFY_MAX_AGE_S
    ensure_database(database)
    assert len(calls) == 1  # at exactly the limit it is checked again
    now[0] += 601.0
    ensure_database(database)
    assert len(calls) == 2  # and again once the renewed verification is past the limit


def test_an_older_smaller_copy_put_in_place_is_verified_again(tmp_path: Path, monkeypatch) -> None:
    """A copy of an earlier state (smaller, older mtime) dropped over the file by hand must not be
    taken for the verified one; the fingerprint is compared for equality, not order."""
    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    earlier = tmp_path / "earlier.db"
    shutil.copy2(database, earlier)  # keeps the older mtime
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE filler (x TEXT)")
        connection.executemany("INSERT INTO filler VALUES (?)", [("z" * 500,)] * 100)
        connection.commit()
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    ensure_database(database)  # the larger, newer file is verified and cached
    calls = _count_verify(monkeypatch)
    shutil.copy2(earlier, database)
    assert database.stat().st_size < runner_module._VERIFIED[str(database.resolve())][0][0]
    ensure_database(database)
    assert len(calls) == 1


def test_a_replaced_corrupt_file_is_still_rejected(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    ensure_database(database)
    good = tmp_path / "good.db"
    shutil.copy2(database, good)
    data = bytearray(database.read_bytes())
    data[100:4096] = b"\x00" * (4096 - 100)
    database.write_bytes(bytes(data))
    with pytest.raises((MigrationError, sqlite3.DatabaseError)):
        ensure_database(database)
    assert runner_module._VERIFIED.get(str(database.resolve())) is None
