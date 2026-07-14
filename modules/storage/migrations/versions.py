"""SotuHire SQLite schema migrations."""

from __future__ import annotations

import sqlite3

from .models import Migration


def _execute_script(connection: sqlite3.Connection, script: str) -> None:
    connection.executescript(f"BEGIN IMMEDIATE;\n{script}")


def _validate_tables(*required: str):
    def validate(connection: sqlite3.Connection) -> list[str]:
        existing = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        return [f"Tabela ausente: {name}" for name in required if name not in existing]

    return validate


def _migration_001(connection: sqlite3.Connection) -> None:
    _execute_script(
        connection,
        """
        CREATE TABLE IF NOT EXISTS schema_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS profile_items (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            confirmed_by_user INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_profile_items_profile ON profile_items(profile_id);
        CREATE INDEX IF NOT EXISTS idx_profile_items_source_ref ON profile_items(source_ref);

        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_memories_source_ref ON memories(source_ref);

        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS captures (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS public_exam_notices (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS public_exam_roles (
            id TEXT PRIMARY KEY,
            notice_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(notice_id) REFERENCES public_exam_notices(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS public_exam_requirements (
            id TEXT PRIMARY KEY,
            role_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(role_id) REFERENCES public_exam_roles(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS radar_wishlists (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS radar_sources (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS radar_runs (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS radar_results (
            id TEXT PRIMARY KEY,
            run_id TEXT,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES radar_runs(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS schedules (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS github_projects (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            source_ref TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        INSERT INTO schema_metadata(key, value) VALUES ('schema_version', '1')
        ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """,
    )


def _migration_002(connection: sqlite3.Connection) -> None:
    _execute_script(
        connection,
        """
        CREATE TABLE IF NOT EXISTS job_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            opportunity_id TEXT,
            title TEXT NOT NULL DEFAULT '',
            organization TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            source_refs TEXT NOT NULL DEFAULT '[]',
            captured_at TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            source_kind TEXT NOT NULL DEFAULT '',
            raw_text TEXT NOT NULL DEFAULT '',
            structured_data TEXT NOT NULL DEFAULT '{}',
            UNIQUE(opportunity_id, content_hash),
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS resume_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            profile_id TEXT,
            resume_variant_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            structured_sections TEXT NOT NULL DEFAULT '{}',
            source_profile_item_ids TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            UNIQUE(profile_id, resume_variant_id, content_hash),
            FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS analysis_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            analysis_type TEXT NOT NULL,
            job_snapshot_id TEXT,
            resume_snapshot_id TEXT,
            provider_requested TEXT NOT NULL DEFAULT 'local',
            provider_used TEXT NOT NULL DEFAULT 'local',
            model_requested TEXT NOT NULL DEFAULT 'local',
            model_used TEXT NOT NULL DEFAULT 'local',
            prompt_id TEXT NOT NULL DEFAULT '',
            prompt_version TEXT NOT NULL DEFAULT '',
            fallback_used INTEGER NOT NULL DEFAULT 0,
            result TEXT NOT NULL DEFAULT '{}',
            evidence_used TEXT NOT NULL DEFAULT '[]',
            source_refs TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            FOREIGN KEY(job_snapshot_id) REFERENCES job_snapshots(snapshot_id),
            FOREIGN KEY(resume_snapshot_id) REFERENCES resume_snapshots(snapshot_id)
        );
        CREATE TABLE IF NOT EXISTS public_exam_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            notice_id TEXT,
            role_id TEXT,
            raw_text TEXT NOT NULL DEFAULT '',
            structured_notice TEXT NOT NULL DEFAULT '{}',
            requirements TEXT NOT NULL DEFAULT '[]',
            timeline TEXT NOT NULL DEFAULT '[]',
            content_hash TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            UNIQUE(notice_id, role_id, content_hash),
            FOREIGN KEY(notice_id) REFERENCES public_exam_notices(id) ON DELETE RESTRICT,
            FOREIGN KEY(role_id) REFERENCES public_exam_roles(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            job_snapshot_id TEXT,
            resume_snapshot_id TEXT,
            tailored_resume_snapshot_id TEXT,
            match_analysis_snapshot_id TEXT,
            ats_analysis_snapshot_id TEXT,
            source_capture_id TEXT,
            job_title TEXT NOT NULL DEFAULT '',
            organization TEXT NOT NULL DEFAULT '',
            source_url TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'found',
            applied_at TEXT,
            stage_history TEXT NOT NULL DEFAULT '[]',
            contact_history TEXT NOT NULL DEFAULT '[]',
            interview_notes TEXT NOT NULL DEFAULT '',
            follow_up_at TEXT,
            outcome TEXT NOT NULL DEFAULT '',
            outcome_reason TEXT NOT NULL DEFAULT '',
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_snapshot_id) REFERENCES job_snapshots(snapshot_id),
            FOREIGN KEY(resume_snapshot_id) REFERENCES resume_snapshots(snapshot_id),
            FOREIGN KEY(tailored_resume_snapshot_id) REFERENCES resume_snapshots(snapshot_id),
            FOREIGN KEY(match_analysis_snapshot_id) REFERENCES analysis_snapshots(snapshot_id),
            FOREIGN KEY(ats_analysis_snapshot_id) REFERENCES analysis_snapshots(snapshot_id),
            FOREIGN KEY(source_capture_id) REFERENCES captures(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS application_events (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_at TEXT NOT NULL,
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
        );

        CREATE TRIGGER IF NOT EXISTS immutable_job_snapshots_update
        BEFORE UPDATE ON job_snapshots BEGIN SELECT RAISE(ABORT, 'job snapshot is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_job_snapshots_delete
        BEFORE DELETE ON job_snapshots BEGIN SELECT RAISE(ABORT, 'job snapshot is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_resume_snapshots_update
        BEFORE UPDATE ON resume_snapshots BEGIN SELECT RAISE(ABORT, 'resume snapshot is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_resume_snapshots_delete
        BEFORE DELETE ON resume_snapshots BEGIN SELECT RAISE(ABORT, 'resume snapshot is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_analysis_snapshots_update
        BEFORE UPDATE ON analysis_snapshots BEGIN SELECT RAISE(ABORT, 'analysis snapshot is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_analysis_snapshots_delete
        BEFORE DELETE ON analysis_snapshots BEGIN SELECT RAISE(ABORT, 'analysis snapshot is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_public_exam_snapshots_update
        BEFORE UPDATE ON public_exam_snapshots BEGIN SELECT RAISE(ABORT, 'public exam snapshot is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_public_exam_snapshots_delete
        BEFORE DELETE ON public_exam_snapshots BEGIN SELECT RAISE(ABORT, 'public exam snapshot is immutable'); END;

        INSERT INTO schema_metadata(key, value) VALUES ('schema_version', '2')
        ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """,
    )


def _migration_003(connection: sqlite3.Connection) -> None:
    _execute_script(
        connection,
        """
        CREATE TABLE IF NOT EXISTS ai_runs (
            run_id TEXT PRIMARY KEY,
            feature TEXT NOT NULL,
            provider_requested TEXT NOT NULL DEFAULT 'local',
            provider_used TEXT NOT NULL DEFAULT 'local',
            model_requested TEXT NOT NULL DEFAULT 'local',
            model_used TEXT NOT NULL DEFAULT 'local',
            prompt_id TEXT NOT NULL DEFAULT '',
            prompt_version TEXT NOT NULL DEFAULT '',
            analysis_mode TEXT NOT NULL DEFAULT 'local',
            fallback_used INTEGER NOT NULL DEFAULT 0,
            fallback_reason TEXT NOT NULL DEFAULT '',
            schema_valid INTEGER NOT NULL DEFAULT 1,
            latency_ms INTEGER,
            token_usage TEXT NOT NULL DEFAULT '{}',
            estimated_cost REAL,
            input_hash TEXT NOT NULL DEFAULT '',
            context_sources TEXT NOT NULL DEFAULT '[]',
            source_refs TEXT NOT NULL DEFAULT '[]',
            evidence_used TEXT NOT NULL DEFAULT '[]',
            warnings TEXT NOT NULL DEFAULT '[]',
            needs_user_review INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ai_runs_feature_created
        ON ai_runs(feature, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_ai_runs_input_hash ON ai_runs(input_hash);

        CREATE TABLE IF NOT EXISTS legacy_migration_history (
            source_path TEXT NOT NULL,
            source_checksum TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            migrated_at TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            PRIMARY KEY(source_path, source_checksum, entity_type, entity_id)
        );

        INSERT INTO schema_metadata(key, value) VALUES ('schema_version', '3')
        ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """,
    )


def _migration_004(connection: sqlite3.Connection) -> None:
    """Add secret-free AI quality, feedback, benchmark and outcome records."""
    columns = {
        "task_id": "TEXT NOT NULL DEFAULT ''",
        "input_schema_version": "TEXT NOT NULL DEFAULT '1'",
        "output_schema_version": "TEXT NOT NULL DEFAULT '1'",
        "context_purpose": "TEXT NOT NULL DEFAULT ''",
        "context_source_types": "TEXT NOT NULL DEFAULT '[]'",
        "context_item_count": "INTEGER NOT NULL DEFAULT 0",
        "evidence_count": "INTEGER NOT NULL DEFAULT 0",
        "started_at": "TEXT NOT NULL DEFAULT ''",
        "finished_at": "TEXT NOT NULL DEFAULT ''",
        "input_tokens": "INTEGER",
        "output_tokens": "INTEGER",
        "total_tokens": "INTEGER",
        "error_type": "TEXT NOT NULL DEFAULT ''",
        "error_message_sanitized": "TEXT NOT NULL DEFAULT ''",
        "benchmark_run_id": "TEXT NOT NULL DEFAULT ''",
        "parent_run_id": "TEXT NOT NULL DEFAULT ''",
    }
    existing = {str(row[1]) for row in connection.execute("PRAGMA table_info(ai_runs)").fetchall()}
    for name, definition in columns.items():
        if name not in existing:
            connection.execute(f"ALTER TABLE ai_runs ADD COLUMN {name} {definition}")
    _execute_script(
        connection,
        """
        CREATE INDEX IF NOT EXISTS idx_ai_runs_task_started
        ON ai_runs(task_id, started_at DESC);
        CREATE INDEX IF NOT EXISTS idx_ai_runs_benchmark
        ON ai_runs(benchmark_run_id);

        CREATE TABLE IF NOT EXISTS ai_feedback (
            feedback_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            rating TEXT NOT NULL,
            decision TEXT NOT NULL,
            edited INTEGER NOT NULL DEFAULT 0,
            unsupported_claim INTEGER NOT NULL DEFAULT 0,
            comment TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES ai_runs(run_id) ON DELETE CASCADE,
            CHECK(rating IN ('useful', 'partial', 'not_useful')),
            CHECK(decision IN ('accepted', 'edited', 'rejected', 'ignored'))
        );
        CREATE INDEX IF NOT EXISTS idx_ai_feedback_run ON ai_feedback(run_id);
        CREATE INDEX IF NOT EXISTS idx_ai_feedback_task_created
        ON ai_feedback(task_id, created_at DESC);

        CREATE TABLE IF NOT EXISTS ai_benchmarks (
            benchmark_run_id TEXT PRIMARY KEY,
            git_sha TEXT NOT NULL DEFAULT '',
            app_version TEXT NOT NULL,
            suite TEXT NOT NULL,
            providers TEXT NOT NULL DEFAULT '[]',
            models TEXT NOT NULL DEFAULT '[]',
            prompt_versions TEXT NOT NULL DEFAULT '{}',
            seed INTEGER NOT NULL,
            dataset_version TEXT NOT NULL,
            environment TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'running'
        );
        CREATE TABLE IF NOT EXISTS ai_benchmark_results (
            result_id TEXT PRIMARY KEY,
            benchmark_run_id TEXT NOT NULL,
            case_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL DEFAULT '',
            prompt_id TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            metrics TEXT NOT NULL DEFAULT '{}',
            latency_ms INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            estimated_cost REAL,
            fallback_used INTEGER NOT NULL DEFAULT 0,
            schema_valid INTEGER NOT NULL DEFAULT 0,
            error_type TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(benchmark_run_id) REFERENCES ai_benchmarks(benchmark_run_id)
                ON DELETE CASCADE,
            UNIQUE(benchmark_run_id, case_id, provider, model)
        );
        CREATE INDEX IF NOT EXISTS idx_ai_benchmark_results_lookup
        ON ai_benchmark_results(task_id, domain, provider);

        CREATE TABLE IF NOT EXISTS outcome_events (
            event_id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT '',
            resume_variant_id TEXT NOT NULL DEFAULT '',
            match_score REAL,
            ats_score REAL,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE,
            CHECK(event_type IN (
                'application_created', 'application_submitted_manually', 'response_received',
                'interview_scheduled', 'interview_completed', 'offer_received', 'rejected',
                'withdrawn', 'no_response'
            ))
        );
        CREATE INDEX IF NOT EXISTS idx_outcome_events_application
        ON outcome_events(application_id, occurred_at);
        CREATE TABLE IF NOT EXISTS outcome_metrics (
            metric_id TEXT PRIMARY KEY,
            scope_type TEXT NOT NULL,
            scope_id TEXT NOT NULL DEFAULT '',
            metric_name TEXT NOT NULL,
            value REAL NOT NULL,
            sample_size INTEGER NOT NULL,
            confidence TEXT NOT NULL,
            calculated_at TEXT NOT NULL,
            UNIQUE(scope_type, scope_id, metric_name)
        );

        INSERT INTO schema_metadata(key, value) VALUES ('schema_version', '4')
        ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """,
    )


MIGRATIONS = (
    Migration(
        version=1,
        description="Entidades locais, proveniência e stores transacionais.",
        up=_migration_001,
        validation=_validate_tables(
            "profiles",
            "profile_items",
            "memories",
            "sources",
            "captures",
            "opportunities",
            "public_exam_notices",
            "radar_wishlists",
            "notifications",
            "github_projects",
        ),
        rollback_strategy="Restaurar o backup pré-migração; arquivos JSON/JSONL não são apagados.",
        created_at="2026-07-12T00:00:00Z",
    ),
    Migration(
        version=2,
        description="Snapshots imutáveis e vínculos completos de candidaturas.",
        up=_migration_002,
        validation=_validate_tables(
            "job_snapshots",
            "resume_snapshots",
            "analysis_snapshots",
            "public_exam_snapshots",
            "applications",
            "application_events",
        ),
        rollback_strategy="Restaurar o backup pré-migração; snapshots não são alterados in-place.",
        created_at="2026-07-12T00:00:00Z",
    ),
    Migration(
        version=3,
        description="Auditoria segura de execuções de IA.",
        up=_migration_003,
        validation=_validate_tables("ai_runs", "legacy_migration_history"),
        rollback_strategy="Restaurar o backup pré-migração ou manter a tabela inativa.",
        created_at="2026-07-12T00:00:00Z",
    ),
    Migration(
        version=4,
        description="Qualidade de IA, feedback humano, benchmarks e outcome learning.",
        up=_migration_004,
        validation=_validate_tables(
            "ai_runs",
            "ai_feedback",
            "ai_benchmarks",
            "ai_benchmark_results",
            "outcome_events",
            "outcome_metrics",
        ),
        rollback_strategy=(
            "Restaurar o backup pré-migração. As tabelas v4 podem permanecer inativas; "
            "nenhum input/output sensível é necessário para recuperação."
        ),
        created_at="2026-07-14T00:00:00Z",
    ),
)

LATEST_SCHEMA_VERSION = MIGRATIONS[-1].version
