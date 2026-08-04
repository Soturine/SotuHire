from __future__ import annotations

import sqlite3

import pytest
from modules.storage.database import connect_database
from modules.storage.migrations import LATEST_SCHEMA_VERSION, MigrationRunner
from modules.storage.migrations.versions import MIGRATIONS


def test_migrations_create_versioned_schema_and_are_idempotent(tmp_path):
    database = tmp_path / "sotuhire.db"
    runner = MigrationRunner(database)

    assert runner.current_version() == 0
    assert runner.apply(create_backup=False) == [1, 2, 3, 4, 5, 6]
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
            "ai_feedback",
            "ai_benchmarks",
            "ai_benchmark_results",
            "outcome_events",
            "outcome_metrics",
            "application_lab_sessions",
            "application_readiness_reports",
            "application_suggestions",
            "master_resumes",
            "resume_sections",
            "resume_entries",
            "resume_variants",
            "resume_variant_changes",
            "resume_templates",
            "resume_exports",
            "application_kits",
            "application_kit_items",
            "application_action_plans",
            "application_action_items",
            "application_analysis_bundles",
            "professional_documents",
            "document_ingestions",
            "professional_assets",
            "scheduler_locks",
            "idempotency_records",
            "migration_history",
        } <= tables
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_v6_backfills_legacy_evidence_review_status(tmp_path):
    database = tmp_path / "sotuhire.db"
    with connect_database(database) as connection:
        MigrationRunner._bootstrap_history(connection)
        for migration in MIGRATIONS[:5]:
            migration.up(connection)
            assert migration.validation(connection) == []
            connection.execute(
                """INSERT INTO migration_history
                (version, description, applied_at, success, validation_errors,
                 rollback_strategy, created_at)
                VALUES (?, ?, '2026-08-03T00:00:00Z', 1, '[]', ?, ?)""",
                (
                    migration.version,
                    migration.description,
                    migration.rollback_strategy,
                    migration.created_at,
                ),
            )
            connection.commit()
        connection.execute(
            """INSERT INTO profiles
            (id, payload, source_ref, content_hash, created_at, updated_at)
            VALUES ('profile-legacy', '{}', '', 'hash', '2026-08-03', '2026-08-03')"""
        )
        connection.executemany(
            """INSERT INTO profile_items
            (id, profile_id, payload, source_ref, content_hash, confirmed_by_user,
             created_at, updated_at)
            VALUES (?, 'profile-legacy', '{}', ?, 'hash', ?, '2026-08-03', '2026-08-03')""",
            [
                ("confirmed", "resume:item:1", 1),
                ("sourced", "github:repo:1", 0),
                ("candidate", "", 0),
            ],
        )
        connection.commit()

    assert MigrationRunner(database).apply(create_backup=False) == [6]
    with connect_database(database) as connection:
        statuses = dict(connection.execute("SELECT id, review_status FROM profile_items"))

    assert statuses == {
        "candidate": "candidate",
        "confirmed": "confirmed",
        "sourced": "sourced",
    }


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
