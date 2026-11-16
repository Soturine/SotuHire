"""Concurrent first use of a new database migrates it once and never reads it half migrated.

Found driving the extension and the web app together (Local Companion + Local API on one data
dir): the first requests all called ensure_database() on a new file, two of them ran every
migration, and a verify in between answered "Schema divergente entre schema_metadata (5) e
migration_history (8)", a 500 on the first screen.
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys
import threading
from collections import Counter
from pathlib import Path

from modules.storage.migrations import forget_verified_databases
from modules.storage.migrations import runner as runner_module

ROOT = Path(__file__).resolve().parents[1]


def test_threads_on_a_new_database_run_each_migration_once(tmp_path: Path, monkeypatch) -> None:
    forget_verified_databases()
    calls: Counter[int] = Counter()

    def counted(migration):
        def up(connection):
            calls[migration.version] += 1
            return migration.up(connection)

        return dataclasses.replace(migration, up=up)

    monkeypatch.setattr(
        runner_module, "MIGRATIONS", tuple(counted(m) for m in runner_module.MIGRATIONS)
    )
    database = tmp_path / "sotuhire.db"
    start = threading.Barrier(6)
    errors: list[BaseException] = []

    def first_request() -> None:
        try:
            start.wait()
            runner_module.MigrationRunner(database).apply(create_backup=False)
            problems = runner_module.MigrationRunner(database).verify()
            if problems:
                raise AssertionError(problems)
        except BaseException as exc:  # noqa: BLE001 - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=first_request) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert set(calls.values()) == {1}, calls
    assert len(calls) == len(runner_module.MIGRATIONS)


def test_processes_sharing_a_data_dir_migrate_it_without_errors(tmp_path: Path) -> None:
    """The Local API and the Local Companion are separate processes over one data dir."""
    database = tmp_path / "shared" / "sotuhire.db"
    code = (
        "import sys\n"
        "from modules.storage.migrations.runner import ensure_database\n"
        "ensure_database(sys.argv[1])\n"
    )
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", code, str(database)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
    results = [proc.communicate(timeout=120) for proc in procs]
    failures = [
        err[-600:] for proc, (_, err) in zip(procs, results, strict=True) if proc.returncode
    ]
    assert failures == []
    assert runner_module.MigrationRunner(database).verify() == []
