from __future__ import annotations

import sqlite3

import pytest
from modules.storage.database import connect_database
from modules.storage.migrations import LATEST_SCHEMA_VERSION, MigrationRunner


def test_migrations_create_versioned_schema_and_are_idempotent(tmp_path):
    database = tmp_path / "sotuhire.db"
    runner = MigrationRunner(database)

    assert runner.current_version() == 0
    assert runner.apply(create_backup=False) == [1, 2, 3]
    assert runner.current_version() == LATEST_SCHEMA_VERSION
    assert runner.apply(create_backup=False) == []
    assert runner.verify() == []

    with connect_database(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {
            "profiles",
            "memories",
            "captures",
            "opportunities",
            "applications",
            "job_snapshots",
            "resume_snapshots",
            "analysis_snapshots",
            "public_exam_snapshots",
            "ai_runs",
            "migration_history",
        } <= tables
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_snapshot_tables_reject_mutation_at_database_level(tmp_path):
    database = tmp_path / "sotuhire.db"
    MigrationRunner(database).apply(create_backup=False)
    with connect_database(database) as connection:
        connection.execute(
            """INSERT INTO job_snapshots
            (snapshot_id, captured_at, content_hash) VALUES ('snapshot-1', '2026-01-01', 'hash')"""
        )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE job_snapshots SET title = 'alterado' WHERE snapshot_id = 'snapshot-1'"
            )


def test_snapshot_parent_deletion_is_restricted_instead_of_mutating_foreign_key(tmp_path):
    database = tmp_path / "sotuhire.db"
    MigrationRunner(database).apply(create_backup=False)
    with connect_database(database) as connection:
        connection.execute(
            """INSERT INTO opportunities
            (id, payload, source_ref, content_hash, created_at, updated_at)
            VALUES ('job-1', '{}', '', 'hash', '2026-01-01', '2026-01-01')"""
        )
        connection.execute(
            """INSERT INTO job_snapshots
            (snapshot_id, opportunity_id, captured_at, content_hash)
            VALUES ('snapshot-1', 'job-1', '2026-01-01', 'hash')"""
        )

        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            connection.execute("DELETE FROM opportunities WHERE id = 'job-1'")

        assert (
            connection.execute(
                "SELECT opportunity_id FROM job_snapshots WHERE snapshot_id = 'snapshot-1'"
            ).fetchone()[0]
            == "job-1"
        )
