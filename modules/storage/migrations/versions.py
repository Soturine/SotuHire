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


def _migration_005(connection: sqlite3.Connection) -> None:
    """Add the guided application lab, resume studio and provider diagnostics."""
    additions = {
        "ai_runs": {
            "provider_error_category": "TEXT NOT NULL DEFAULT ''",
            "error_code": "TEXT NOT NULL DEFAULT ''",
            "request_id": "TEXT NOT NULL DEFAULT ''",
            "retry_after_seconds": "REAL",
            "attempt": "INTEGER NOT NULL DEFAULT 1",
            "max_attempts": "INTEGER NOT NULL DEFAULT 1",
            "repaired": "INTEGER NOT NULL DEFAULT 0",
            "repair_reason": "TEXT NOT NULL DEFAULT ''",
            "degraded_mode": "INTEGER NOT NULL DEFAULT 0",
        },
        "ai_benchmark_results": {
            "diagnostics": "TEXT NOT NULL DEFAULT '{}'",
        },
        "applications": {
            "application_lab_session_id": "TEXT",
            "readiness_report_id": "TEXT",
            "resume_variant_id": "TEXT",
            "application_kit_id": "TEXT",
            "action_plan_id": "TEXT",
            "lab_analysis_snapshot_id": "TEXT",
            "application_kit_snapshot_id": "TEXT",
        },
    }
    for table, columns in additions.items():
        existing = {
            str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    _execute_script(
        connection,
        """
        CREATE TABLE IF NOT EXISTS master_resumes (
            master_resume_id TEXT PRIMARY KEY,
            profile_id TEXT,
            title TEXT NOT NULL,
            target_role TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            raw_text TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT 'manual',
            source_refs TEXT NOT NULL DEFAULT '[]',
            source_profile_item_ids TEXT NOT NULL DEFAULT '[]',
            validation_warnings TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_master_resumes_profile_updated
        ON master_resumes(profile_id, updated_at DESC);

        CREATE TABLE IF NOT EXISTS resume_sections (
            section_id TEXT PRIMARY KEY,
            master_resume_id TEXT NOT NULL,
            section_type TEXT NOT NULL,
            title TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            content TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(master_resume_id) REFERENCES master_resumes(master_resume_id)
                ON DELETE CASCADE,
            UNIQUE(master_resume_id, section_type, position)
        );
        CREATE INDEX IF NOT EXISTS idx_resume_sections_master_position
        ON resume_sections(master_resume_id, position);

        CREATE TABLE IF NOT EXISTS resume_entries (
            entry_id TEXT PRIMARY KEY,
            section_id TEXT NOT NULL,
            entry_type TEXT NOT NULL DEFAULT 'item',
            title TEXT NOT NULL DEFAULT '',
            subtitle TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            start_date TEXT NOT NULL DEFAULT '',
            end_date TEXT NOT NULL DEFAULT '',
            position INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            source_profile_item_ids TEXT NOT NULL DEFAULT '[]',
            source_refs TEXT NOT NULL DEFAULT '[]',
            confirmed_by_user INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(section_id) REFERENCES resume_sections(section_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_resume_entries_section_position
        ON resume_entries(section_id, position);

        CREATE TABLE IF NOT EXISTS resume_variants (
            resume_variant_id TEXT PRIMARY KEY,
            master_resume_id TEXT NOT NULL,
            job_snapshot_id TEXT,
            title TEXT NOT NULL,
            target_role TEXT NOT NULL DEFAULT '',
            sections TEXT NOT NULL DEFAULT '[]',
            source_profile_item_ids TEXT NOT NULL DEFAULT '[]',
            change_set TEXT NOT NULL DEFAULT '[]',
            validation_warnings TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(master_resume_id) REFERENCES master_resumes(master_resume_id)
                ON DELETE CASCADE,
            FOREIGN KEY(job_snapshot_id) REFERENCES job_snapshots(snapshot_id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_resume_variants_master_updated
        ON resume_variants(master_resume_id, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_resume_variants_job
        ON resume_variants(job_snapshot_id);

        CREATE TABLE IF NOT EXISTS resume_variant_changes (
            change_id TEXT PRIMARY KEY,
            resume_variant_id TEXT NOT NULL,
            change_type TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT '',
            before_value TEXT NOT NULL DEFAULT '',
            after_value TEXT NOT NULL DEFAULT '',
            reason TEXT NOT NULL DEFAULT '',
            evidence_used TEXT NOT NULL DEFAULT '[]',
            source_refs TEXT NOT NULL DEFAULT '[]',
            warning TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(resume_variant_id) REFERENCES resume_variants(resume_variant_id)
                ON DELETE CASCADE,
            CHECK(change_type IN ('added', 'removed', 'edited', 'reordered'))
        );
        CREATE INDEX IF NOT EXISTS idx_resume_variant_changes_variant
        ON resume_variant_changes(resume_variant_id, created_at);

        CREATE TABLE IF NOT EXISTS resume_templates (
            template_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            ats_safe INTEGER NOT NULL DEFAULT 1,
            page_sizes TEXT NOT NULL DEFAULT '["A4", "Letter"]',
            configuration TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS resume_exports (
            export_id TEXT PRIMARY KEY,
            master_resume_id TEXT,
            resume_variant_id TEXT,
            template_id TEXT,
            format TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ready',
            file_name TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            warnings TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY(master_resume_id) REFERENCES master_resumes(master_resume_id)
                ON DELETE CASCADE,
            FOREIGN KEY(resume_variant_id) REFERENCES resume_variants(resume_variant_id)
                ON DELETE CASCADE,
            FOREIGN KEY(template_id) REFERENCES resume_templates(template_id) ON DELETE SET NULL,
            CHECK(format IN ('json_resume', 'pdf', 'docx')),
            CHECK(status IN ('ready', 'pending', 'failed'))
        );

        CREATE TABLE IF NOT EXISTS application_lab_sessions (
            session_id TEXT PRIMARY KEY,
            profile_id TEXT,
            master_resume_id TEXT,
            job_id TEXT NOT NULL DEFAULT '',
            job_snapshot_id TEXT,
            current_step INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'draft',
            selected_context_refs TEXT NOT NULL DEFAULT '[]',
            analysis_run_ids TEXT NOT NULL DEFAULT '[]',
            readiness_report_id TEXT,
            resume_variant_id TEXT,
            application_kit_id TEXT,
            action_plan_id TEXT,
            tracker_application_id TEXT,
            invalidated_steps TEXT NOT NULL DEFAULT '[]',
            warnings TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE SET NULL,
            FOREIGN KEY(master_resume_id) REFERENCES master_resumes(master_resume_id)
                ON DELETE SET NULL,
            FOREIGN KEY(job_snapshot_id) REFERENCES job_snapshots(snapshot_id) ON DELETE SET NULL,
            FOREIGN KEY(resume_variant_id) REFERENCES resume_variants(resume_variant_id)
                ON DELETE SET NULL,
            FOREIGN KEY(tracker_application_id) REFERENCES applications(id) ON DELETE SET NULL,
            CHECK(current_step BETWEEN 1 AND 10),
            CHECK(status IN ('draft', 'ready', 'analyzing', 'review', 'completed',
                             'cancelled', 'failed'))
        );
        CREATE INDEX IF NOT EXISTS idx_application_lab_sessions_updated
        ON application_lab_sessions(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_application_lab_sessions_profile
        ON application_lab_sessions(profile_id, updated_at DESC);

        CREATE TABLE IF NOT EXISTS application_readiness_reports (
            report_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            readiness_score REAL NOT NULL,
            score_explanation TEXT NOT NULL DEFAULT '',
            evidence_coverage REAL NOT NULL DEFAULT 0,
            requirement_coverage REAL NOT NULL DEFAULT 0,
            source_dimensions TEXT NOT NULL DEFAULT '{}',
            strengths TEXT NOT NULL DEFAULT '[]',
            top_blockers TEXT NOT NULL DEFAULT '[]',
            missing_information TEXT NOT NULL DEFAULT '[]',
            unsupported_claim_risks TEXT NOT NULL DEFAULT '[]',
            recommended_edits TEXT NOT NULL DEFAULT '[]',
            copy_ready_snippets TEXT NOT NULL DEFAULT '[]',
            action_plan_preview TEXT NOT NULL DEFAULT '[]',
            warnings TEXT NOT NULL DEFAULT '[]',
            provider_metadata TEXT NOT NULL DEFAULT '{}',
            evidence_used TEXT NOT NULL DEFAULT '[]',
            perspectives TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES application_lab_sessions(session_id)
                ON DELETE CASCADE,
            CHECK(readiness_score BETWEEN 0 AND 100),
            CHECK(evidence_coverage BETWEEN 0 AND 1),
            CHECK(requirement_coverage BETWEEN 0 AND 1)
        );

        CREATE TABLE IF NOT EXISTS application_suggestions (
            suggestion_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            suggestion_type TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT '',
            before_value TEXT NOT NULL DEFAULT '',
            after_value TEXT NOT NULL DEFAULT '',
            reason TEXT NOT NULL DEFAULT '',
            evidence_used TEXT NOT NULL DEFAULT '[]',
            source_refs TEXT NOT NULL DEFAULT '[]',
            warnings TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'pending',
            edited_value TEXT NOT NULL DEFAULT '',
            provider_run_id TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            FOREIGN KEY(session_id) REFERENCES application_lab_sessions(session_id)
                ON DELETE CASCADE,
            CHECK(status IN ('pending', 'accepted', 'edited', 'rejected'))
        );
        CREATE INDEX IF NOT EXISTS idx_application_suggestions_session_status
        ON application_suggestions(session_id, status, created_at);

        CREATE TABLE IF NOT EXISTS application_kits (
            application_kit_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL DEFAULT '',
            warnings TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES application_lab_sessions(session_id)
                ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS application_kit_items (
            item_id TEXT PRIMARY KEY,
            application_kit_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            evidence_used TEXT NOT NULL DEFAULT '[]',
            warnings TEXT NOT NULL DEFAULT '[]',
            provider_run_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            edited_content TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(application_kit_id) REFERENCES application_kits(application_kit_id)
                ON DELETE CASCADE,
            CHECK(status IN ('pending', 'accepted', 'edited', 'rejected'))
        );

        CREATE TABLE IF NOT EXISTS application_action_plans (
            action_plan_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            period_days INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES application_lab_sessions(session_id)
                ON DELETE CASCADE,
            CHECK(period_days IN (7, 14, 30))
        );
        CREATE TABLE IF NOT EXISTS application_action_items (
            action_item_id TEXT PRIMARY KEY,
            action_plan_id TEXT NOT NULL,
            title TEXT NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'medium',
            due_at TEXT,
            related_gap TEXT NOT NULL DEFAULT '',
            related_evidence TEXT NOT NULL DEFAULT '[]',
            estimated_effort TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY(action_plan_id) REFERENCES application_action_plans(action_plan_id)
                ON DELETE CASCADE,
            CHECK(priority IN ('low', 'medium', 'high')),
            CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled'))
        );
        CREATE INDEX IF NOT EXISTS idx_application_action_items_plan_status
        ON application_action_items(action_plan_id, status, due_at);

        INSERT OR IGNORE INTO resume_templates
        (template_id, name, description, ats_safe, page_sizes, configuration, created_at, updated_at)
        VALUES
        ('classic', 'Clássico', 'Hierarquia simples e leitura linear.', 1,
         '["A4", "Letter"]', '{"density":"comfortable"}', '2026-07-28T00:00:00Z', '2026-07-28T00:00:00Z'),
        ('compact', 'Compacto', 'Mais conteúdo sem tabelas complexas.', 1,
         '["A4", "Letter"]', '{"density":"compact"}', '2026-07-28T00:00:00Z', '2026-07-28T00:00:00Z'),
        ('technical', 'Técnico', 'Projetos e competências com semântica ATS.', 1,
         '["A4", "Letter"]', '{"emphasis":"projects"}', '2026-07-28T00:00:00Z', '2026-07-28T00:00:00Z'),
        ('academic', 'Acadêmico', 'Formação e produção em ordem clara.', 1,
         '["A4", "Letter"]', '{"emphasis":"academic"}', '2026-07-28T00:00:00Z', '2026-07-28T00:00:00Z');

        INSERT INTO schema_metadata(key, value) VALUES ('schema_version', '5')
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
    Migration(
        version=5,
        description=(
            "Application Lab, Resume Studio, sugestões revisáveis e diagnósticos de provider."
        ),
        up=_migration_005,
        validation=_validate_tables(
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
        ),
        rollback_strategy=(
            "Restaurar o backup pré-migração. Stores JSON/JSONL e snapshots anteriores "
            "permanecem preservados."
        ),
        created_at="2026-07-28T00:00:00Z",
    ),
)

LATEST_SCHEMA_VERSION = MIGRATIONS[-1].version
