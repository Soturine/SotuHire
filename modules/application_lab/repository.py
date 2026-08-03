"""SQLite repository for guided application and resume-studio state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.application_lab.models import (
    ActionPlanItem,
    ApplicationActionPlan,
    ApplicationKit,
    ApplicationKitItem,
    ApplicationLabSession,
    ApplicationReadinessReport,
    ApplicationSuggestion,
    MasterResume,
    ReadinessDimension,
    ReadinessPerspective,
    ResumeEntry,
    ResumeExport,
    ResumeSection,
    ResumeTemplate,
    ResumeVariant,
    ResumeVariantChange,
    SuggestionStatus,
    utc_now,
)
from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database


class ApplicationLabRepository:
    """Persist resumable Lab state without duplicating existing analysis engines."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def save_master_resume(self, resume: MasterResume) -> MasterResume:
        resume = resume.model_copy(deep=True)
        _normalize_positions(resume.sections)
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            if resume.profile_id:
                now = resume.updated_at.isoformat()
                connection.execute(
                    """INSERT OR IGNORE INTO profiles
                    (id, payload, source_ref, content_hash, created_at, updated_at)
                    VALUES (?, ?, '', '', ?, ?)""",
                    (resume.profile_id, _json({"id": resume.profile_id}), now, now),
                )
            connection.execute(
                """INSERT INTO master_resumes
                (master_resume_id, profile_id, title, target_role, summary, raw_text,
                 source_type, source_refs, source_profile_item_ids, validation_warnings,
                 created_at, updated_at)
                VALUES (?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(master_resume_id) DO UPDATE SET
                    profile_id=excluded.profile_id, title=excluded.title,
                    target_role=excluded.target_role, summary=excluded.summary,
                    raw_text=excluded.raw_text, source_type=excluded.source_type,
                    source_refs=excluded.source_refs,
                    source_profile_item_ids=excluded.source_profile_item_ids,
                    validation_warnings=excluded.validation_warnings,
                    updated_at=excluded.updated_at""",
                (
                    resume.master_resume_id,
                    resume.profile_id,
                    resume.title,
                    resume.target_role,
                    resume.summary,
                    resume.raw_text,
                    resume.source_type,
                    _json(resume.source_refs),
                    _json(resume.source_profile_item_ids),
                    _json(resume.validation_warnings),
                    resume.created_at.isoformat(),
                    resume.updated_at.isoformat(),
                ),
            )
            connection.execute(
                "DELETE FROM resume_sections WHERE master_resume_id = ?",
                (resume.master_resume_id,),
            )
            for section in resume.sections:
                connection.execute(
                    """INSERT INTO resume_sections
                    (section_id, master_resume_id, section_type, title, position, enabled,
                     content, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        section.section_id,
                        resume.master_resume_id,
                        section.section_type,
                        section.title,
                        section.position,
                        int(section.enabled),
                        section.content,
                        section.created_at.isoformat(),
                        section.updated_at.isoformat(),
                    ),
                )
                for entry in section.entries:
                    connection.execute(
                        """INSERT INTO resume_entries
                        (entry_id, section_id, entry_type, title, subtitle, content,
                         start_date, end_date, position, enabled, source_profile_item_ids,
                         source_refs, confirmed_by_user, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            entry.entry_id,
                            section.section_id,
                            entry.entry_type,
                            entry.title,
                            entry.subtitle,
                            entry.content,
                            entry.start_date,
                            entry.end_date,
                            entry.position,
                            int(entry.enabled),
                            _json(entry.source_profile_item_ids),
                            _json(entry.source_refs),
                            int(entry.confirmed_by_user),
                            entry.created_at.isoformat(),
                            entry.updated_at.isoformat(),
                        ),
                    )
        return resume

    def get_master_resume(self, master_resume_id: str = "") -> MasterResume | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            if master_resume_id:
                row = connection.execute(
                    "SELECT * FROM master_resumes WHERE master_resume_id = ?",
                    (master_resume_id,),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM master_resumes ORDER BY updated_at DESC LIMIT 1"
                ).fetchone()
            if row is None:
                return None
            section_rows = connection.execute(
                """SELECT * FROM resume_sections WHERE master_resume_id = ?
                ORDER BY position, section_id""",
                (row["master_resume_id"],),
            ).fetchall()
            sections: list[ResumeSection] = []
            for section_row in section_rows:
                entry_rows = connection.execute(
                    """SELECT * FROM resume_entries WHERE section_id = ?
                    ORDER BY position, entry_id""",
                    (section_row["section_id"],),
                ).fetchall()
                sections.append(_section_from_rows(section_row, entry_rows))
        return MasterResume(
            master_resume_id=row["master_resume_id"],
            profile_id=row["profile_id"] or "",
            title=row["title"],
            target_role=row["target_role"],
            summary=row["summary"],
            raw_text=row["raw_text"],
            source_type=row["source_type"],
            source_refs=_load(row["source_refs"], []),
            source_profile_item_ids=_load(row["source_profile_item_ids"], []),
            sections=sections,
            validation_warnings=_load(row["validation_warnings"], []),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_variant(self, variant: ResumeVariant) -> ResumeVariant:
        variant = variant.model_copy(deep=True)
        _normalize_positions(variant.sections)
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO resume_variants
                (resume_variant_id, master_resume_id, job_snapshot_id, title, target_role,
                 sections, source_profile_item_ids, change_set, validation_warnings,
                 created_at, updated_at)
                VALUES (?, ?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(resume_variant_id) DO UPDATE SET
                    job_snapshot_id=excluded.job_snapshot_id, title=excluded.title,
                    target_role=excluded.target_role, sections=excluded.sections,
                    source_profile_item_ids=excluded.source_profile_item_ids,
                    change_set=excluded.change_set,
                    validation_warnings=excluded.validation_warnings,
                    updated_at=excluded.updated_at""",
                (
                    variant.resume_variant_id,
                    variant.master_resume_id,
                    variant.job_snapshot_id,
                    variant.title,
                    variant.target_role,
                    _json([item.model_dump(mode="json") for item in variant.sections]),
                    _json(variant.source_profile_item_ids),
                    _json([item.model_dump(mode="json") for item in variant.change_set]),
                    _json(variant.validation_warnings),
                    variant.created_at.isoformat(),
                    variant.updated_at.isoformat(),
                ),
            )
            connection.execute(
                "DELETE FROM resume_variant_changes WHERE resume_variant_id = ?",
                (variant.resume_variant_id,),
            )
            for change in variant.change_set:
                connection.execute(
                    """INSERT INTO resume_variant_changes
                    (change_id, resume_variant_id, change_type, section, before_value,
                     after_value, reason, evidence_used, source_refs, warning, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        change.change_id,
                        variant.resume_variant_id,
                        change.change_type,
                        change.section,
                        change.before,
                        change.after,
                        change.reason,
                        _json(change.evidence_used),
                        _json(change.source_refs),
                        change.warning,
                        change.created_at.isoformat(),
                    ),
                )
        return variant

    def get_variant(self, resume_variant_id: str) -> ResumeVariant | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM resume_variants WHERE resume_variant_id = ?",
                (resume_variant_id,),
            ).fetchone()
        return _variant_from_row(row) if row is not None else None

    def list_variants(
        self, *, master_resume_id: str = "", limit: int = 50, offset: int = 0
    ) -> list[ResumeVariant]:
        ensure_database(self.database_path)
        bounded_limit, bounded_offset = _page(limit, offset)
        with connect_database(self.database_path) as connection:
            if master_resume_id:
                rows = connection.execute(
                    """SELECT * FROM resume_variants WHERE master_resume_id = ?
                    ORDER BY updated_at DESC LIMIT ? OFFSET ?""",
                    (master_resume_id, bounded_limit, bounded_offset),
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT * FROM resume_variants ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?""",
                    (bounded_limit, bounded_offset),
                ).fetchall()
        return [_variant_from_row(row) for row in rows]

    def count_variants(self, *, master_resume_id: str = "") -> int:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            if master_resume_id:
                row = connection.execute(
                    "SELECT COUNT(*) AS total FROM resume_variants WHERE master_resume_id = ?",
                    (master_resume_id,),
                ).fetchone()
            else:
                row = connection.execute("SELECT COUNT(*) AS total FROM resume_variants").fetchone()
        return int(row["total"]) if row is not None else 0

    def list_templates(self) -> list[ResumeTemplate]:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM resume_templates ORDER BY template_id"
            ).fetchall()
        return [
            ResumeTemplate(
                template_id=row["template_id"],
                name=row["name"],
                description=row["description"],
                ats_safe=bool(row["ats_safe"]),
                page_sizes=_load(row["page_sizes"], ["A4", "Letter"]),
                configuration=_load(row["configuration"], {}),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def save_export(self, export: ResumeExport) -> ResumeExport:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO resume_exports
                (export_id, master_resume_id, resume_variant_id, template_id, format,
                 status, file_name, content_hash, warnings, created_at)
                VALUES (?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''), ?, ?, ?, ?, ?, ?)""",
                (
                    export.export_id,
                    export.master_resume_id,
                    export.resume_variant_id,
                    export.template_id,
                    export.format,
                    export.status,
                    export.file_name,
                    export.content_hash,
                    _json(export.warnings),
                    export.created_at.isoformat(),
                ),
            )
        return export

    def save_session(self, session: ApplicationLabSession) -> ApplicationLabSession:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO application_lab_sessions
                (session_id, profile_id, master_resume_id, job_id, job_snapshot_id,
                 current_step, status, selected_context_refs, analysis_run_ids,
                 readiness_report_id, resume_variant_id, application_kit_id,
                 action_plan_id, tracker_application_id, invalidated_steps, warnings,
                 created_at, updated_at, completed_at)
                VALUES (?, NULLIF(?, ''), NULLIF(?, ''), ?, NULLIF(?, ''), ?, ?, ?, ?,
                        NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''),
                        NULLIF(?, ''), ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    profile_id=excluded.profile_id,
                    master_resume_id=excluded.master_resume_id,
                    job_id=excluded.job_id,
                    job_snapshot_id=excluded.job_snapshot_id,
                    current_step=excluded.current_step,
                    status=excluded.status,
                    selected_context_refs=excluded.selected_context_refs,
                    analysis_run_ids=excluded.analysis_run_ids,
                    readiness_report_id=excluded.readiness_report_id,
                    resume_variant_id=excluded.resume_variant_id,
                    application_kit_id=excluded.application_kit_id,
                    action_plan_id=excluded.action_plan_id,
                    tracker_application_id=excluded.tracker_application_id,
                    invalidated_steps=excluded.invalidated_steps,
                    warnings=excluded.warnings,
                    updated_at=excluded.updated_at,
                    completed_at=excluded.completed_at""",
                (
                    session.session_id,
                    session.profile_id,
                    session.master_resume_id,
                    session.job_id,
                    session.job_snapshot_id,
                    session.current_step,
                    session.status,
                    _json(session.selected_context_refs),
                    _json(session.analysis_run_ids),
                    session.readiness_report_id,
                    session.resume_variant_id,
                    session.application_kit_id,
                    session.action_plan_id,
                    session.tracker_application_id,
                    _json(session.invalidated_steps),
                    _json(session.warnings),
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    session.completed_at.isoformat() if session.completed_at else None,
                ),
            )
        return session

    def get_session(self, session_id: str) -> ApplicationLabSession | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM application_lab_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return _session_from_row(row) if row is not None else None

    def list_sessions(self, *, limit: int = 50, offset: int = 0) -> list[ApplicationLabSession]:
        ensure_database(self.database_path)
        bounded_limit, bounded_offset = _page(limit, offset)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """SELECT * FROM application_lab_sessions ORDER BY updated_at DESC
                LIMIT ? OFFSET ?""",
                (bounded_limit, bounded_offset),
            ).fetchall()
        return [_session_from_row(row) for row in rows]

    def count_sessions(self) -> int:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM application_lab_sessions"
            ).fetchone()
        return int(row["total"]) if row is not None else 0

    def save_report(self, report: ApplicationReadinessReport) -> ApplicationReadinessReport:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO application_readiness_reports
                (report_id, session_id, readiness_score, score_explanation,
                 evidence_coverage, requirement_coverage, evidence_coverage_value,
                 requirement_coverage_value, confidence_score, risk_score,
                 assessment_status, unknown_dimension_count, source_dimensions, strengths,
                 top_blockers, missing_information, unsupported_claim_risks,
                 recommended_edits, copy_ready_snippets, action_plan_preview, warnings,
                 provider_metadata, evidence_used, perspectives, dependency_hash,
                 stale_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    report_id=excluded.report_id,
                    readiness_score=excluded.readiness_score,
                    score_explanation=excluded.score_explanation,
                    evidence_coverage=excluded.evidence_coverage,
                    requirement_coverage=excluded.requirement_coverage,
                    evidence_coverage_value=excluded.evidence_coverage_value,
                    requirement_coverage_value=excluded.requirement_coverage_value,
                    confidence_score=excluded.confidence_score,
                    risk_score=excluded.risk_score,
                    assessment_status=excluded.assessment_status,
                    unknown_dimension_count=excluded.unknown_dimension_count,
                    source_dimensions=excluded.source_dimensions,
                    strengths=excluded.strengths,
                    top_blockers=excluded.top_blockers,
                    missing_information=excluded.missing_information,
                    unsupported_claim_risks=excluded.unsupported_claim_risks,
                    recommended_edits=excluded.recommended_edits,
                    copy_ready_snippets=excluded.copy_ready_snippets,
                    action_plan_preview=excluded.action_plan_preview,
                    warnings=excluded.warnings,
                    provider_metadata=excluded.provider_metadata,
                    evidence_used=excluded.evidence_used,
                    perspectives=excluded.perspectives,
                    dependency_hash=excluded.dependency_hash,
                    stale_reason=excluded.stale_reason,
                    created_at=excluded.created_at""",
                (
                    report.report_id,
                    report.session_id,
                    report.readiness_score,
                    report.score_explanation,
                    report.evidence_coverage,
                    report.requirement_coverage,
                    report.evidence_coverage_value,
                    report.requirement_coverage_value,
                    report.confidence_score,
                    report.risk_score,
                    report.assessment_status,
                    report.unknown_dimension_count,
                    _json(
                        {
                            key: value.model_dump(mode="json")
                            for key, value in report.source_dimensions.items()
                        }
                    ),
                    _json(report.strengths),
                    _json(report.top_blockers),
                    _json(report.missing_information),
                    _json(report.unsupported_claim_risks),
                    _json(report.recommended_edits),
                    _json(report.copy_ready_snippets),
                    _json(report.action_plan_preview),
                    _json(report.warnings),
                    _json(report.provider_metadata),
                    _json(report.evidence_used),
                    _json(
                        {
                            key: value.model_dump(mode="json")
                            for key, value in report.perspectives.items()
                        }
                    ),
                    report.dependency_hash,
                    report.stale_reason,
                    report.created_at.isoformat(),
                ),
            )
            connection.execute(
                """UPDATE application_lab_sessions
                SET readiness_report_id = ?, updated_at = ? WHERE session_id = ?""",
                (report.report_id, utc_now().isoformat(), report.session_id),
            )
        return report

    def get_report(
        self, report_id: str = "", *, session_id: str = ""
    ) -> ApplicationReadinessReport | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            if report_id:
                row = connection.execute(
                    "SELECT * FROM application_readiness_reports WHERE report_id = ?",
                    (report_id,),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM application_readiness_reports WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
        return _report_from_row(row) if row is not None else None

    def save_suggestions(
        self, suggestions: list[ApplicationSuggestion]
    ) -> list[ApplicationSuggestion]:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            for item in suggestions:
                connection.execute(
                    """INSERT INTO application_suggestions
                    (suggestion_id, session_id, suggestion_type, section, before_value,
                     after_value, reason, evidence_used, source_refs, warnings, status,
                     edited_value, provider_run_id, created_at, reviewed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(suggestion_id) DO UPDATE SET
                        after_value=excluded.after_value, reason=excluded.reason,
                        evidence_used=excluded.evidence_used, source_refs=excluded.source_refs,
                        warnings=excluded.warnings, status=excluded.status,
                        edited_value=excluded.edited_value,
                        provider_run_id=excluded.provider_run_id,
                        reviewed_at=excluded.reviewed_at""",
                    (
                        item.suggestion_id,
                        item.session_id,
                        item.suggestion_type,
                        item.section,
                        item.before,
                        item.after,
                        item.reason,
                        _json(item.evidence_used),
                        _json(item.source_refs),
                        _json(item.warnings),
                        item.status,
                        item.edited_value,
                        item.provider_run_id,
                        item.created_at.isoformat(),
                        item.reviewed_at.isoformat() if item.reviewed_at else None,
                    ),
                )
        return suggestions

    def replace_pending_suggestions(
        self, session_id: str, suggestions: list[ApplicationSuggestion]
    ) -> list[ApplicationSuggestion]:
        """Replace only unreviewed drafts while preserving every human decision."""
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """DELETE FROM application_suggestions
                WHERE session_id = ? AND status = 'pending'""",
                (session_id,),
            )
        return self.save_suggestions(suggestions)

    def list_suggestions(self, session_id: str) -> list[ApplicationSuggestion]:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """SELECT * FROM application_suggestions WHERE session_id = ?
                ORDER BY created_at, suggestion_id""",
                (session_id,),
            ).fetchall()
        return [_suggestion_from_row(row) for row in rows]

    def get_suggestion(self, suggestion_id: str) -> ApplicationSuggestion | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM application_suggestions WHERE suggestion_id = ?",
                (suggestion_id,),
            ).fetchone()
        return _suggestion_from_row(row) if row is not None else None

    def review_suggestion(
        self,
        suggestion_id: str,
        status: SuggestionStatus,
        *,
        edited_value: str = "",
    ) -> ApplicationSuggestion | None:
        item = self.get_suggestion(suggestion_id)
        if item is None:
            return None
        updated = item.model_copy(
            update={"status": status, "edited_value": edited_value, "reviewed_at": utc_now()}
        )
        self.save_suggestions([updated])
        return updated

    def save_kit(self, kit: ApplicationKit) -> ApplicationKit:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO application_kits
                (application_kit_id, session_id, title, warnings, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    application_kit_id=excluded.application_kit_id,
                    title=excluded.title, warnings=excluded.warnings,
                    updated_at=excluded.updated_at""",
                (
                    kit.application_kit_id,
                    kit.session_id,
                    kit.title,
                    _json(kit.warnings),
                    kit.created_at.isoformat(),
                    kit.updated_at.isoformat(),
                ),
            )
            connection.execute(
                "DELETE FROM application_kit_items WHERE application_kit_id = ?",
                (kit.application_kit_id,),
            )
            for item in kit.items:
                connection.execute(
                    """INSERT INTO application_kit_items
                    (item_id, application_kit_id, item_type, content, evidence_used,
                     warnings, provider_run_id, status, edited_content, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.item_id,
                        kit.application_kit_id,
                        item.type,
                        item.content,
                        _json(item.evidence_used),
                        _json(item.warnings),
                        item.provider_run_id,
                        item.status,
                        item.edited_content,
                        item.created_at.isoformat(),
                        item.updated_at.isoformat(),
                    ),
                )
            connection.execute(
                """UPDATE application_lab_sessions SET application_kit_id = ?, updated_at = ?
                WHERE session_id = ?""",
                (kit.application_kit_id, utc_now().isoformat(), kit.session_id),
            )
        return kit

    def get_kit(self, application_kit_id: str) -> ApplicationKit | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM application_kits WHERE application_kit_id = ?",
                (application_kit_id,),
            ).fetchone()
            if row is None:
                return None
            items = connection.execute(
                """SELECT * FROM application_kit_items WHERE application_kit_id = ?
                ORDER BY created_at, item_id""",
                (application_kit_id,),
            ).fetchall()
        return ApplicationKit(
            application_kit_id=row["application_kit_id"],
            session_id=row["session_id"],
            title=row["title"],
            warnings=_load(row["warnings"], []),
            items=[_kit_item_from_row(item) for item in items],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_action_plan(self, plan: ApplicationActionPlan) -> ApplicationActionPlan:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO application_action_plans
                (action_plan_id, session_id, period_days, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    action_plan_id=excluded.action_plan_id,
                    period_days=excluded.period_days, title=excluded.title,
                    updated_at=excluded.updated_at""",
                (
                    plan.action_plan_id,
                    plan.session_id,
                    plan.period_days,
                    plan.title,
                    plan.created_at.isoformat(),
                    plan.updated_at.isoformat(),
                ),
            )
            connection.execute(
                "DELETE FROM application_action_items WHERE action_plan_id = ?",
                (plan.action_plan_id,),
            )
            for item in plan.items:
                connection.execute(
                    """INSERT INTO application_action_items
                    (action_item_id, action_plan_id, title, reason, priority, due_at,
                     related_gap, related_evidence, estimated_effort, status,
                     created_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.action_item_id,
                        plan.action_plan_id,
                        item.title,
                        item.reason,
                        item.priority,
                        item.due_at.isoformat() if item.due_at else None,
                        item.related_gap,
                        _json(item.related_evidence),
                        item.estimated_effort,
                        item.status,
                        item.created_at.isoformat(),
                        item.completed_at.isoformat() if item.completed_at else None,
                    ),
                )
            connection.execute(
                """UPDATE application_lab_sessions SET action_plan_id = ?, updated_at = ?
                WHERE session_id = ?""",
                (plan.action_plan_id, utc_now().isoformat(), plan.session_id),
            )
        return plan

    def get_action_plan(self, action_plan_id: str) -> ApplicationActionPlan | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM application_action_plans WHERE action_plan_id = ?",
                (action_plan_id,),
            ).fetchone()
            if row is None:
                return None
            items = connection.execute(
                """SELECT * FROM application_action_items WHERE action_plan_id = ?
                ORDER BY due_at, created_at""",
                (action_plan_id,),
            ).fetchall()
        return ApplicationActionPlan(
            action_plan_id=row["action_plan_id"],
            session_id=row["session_id"],
            period_days=row["period_days"],
            title=row["title"],
            items=[_action_item_from_row(item) for item in items],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def _section_from_rows(section: Any, entries: list[Any]) -> ResumeSection:
    return ResumeSection(
        section_id=section["section_id"],
        section_type=section["section_type"],
        title=section["title"],
        position=section["position"],
        enabled=bool(section["enabled"]),
        content=section["content"],
        entries=[
            ResumeEntry(
                entry_id=row["entry_id"],
                entry_type=row["entry_type"],
                title=row["title"],
                subtitle=row["subtitle"],
                content=row["content"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                position=row["position"],
                enabled=bool(row["enabled"]),
                source_profile_item_ids=_load(row["source_profile_item_ids"], []),
                source_refs=_load(row["source_refs"], []),
                confirmed_by_user=bool(row["confirmed_by_user"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in entries
        ],
        created_at=section["created_at"],
        updated_at=section["updated_at"],
    )


def _normalize_positions(sections: list[ResumeSection]) -> None:
    for section_position, section in enumerate(sections):
        section.position = section_position
        for entry_position, entry in enumerate(section.entries):
            entry.position = entry_position


def _variant_from_row(row: Any) -> ResumeVariant:
    return ResumeVariant(
        resume_variant_id=row["resume_variant_id"],
        master_resume_id=row["master_resume_id"],
        job_snapshot_id=row["job_snapshot_id"] or "",
        title=row["title"],
        target_role=row["target_role"],
        sections=[ResumeSection.model_validate(item) for item in _load(row["sections"], [])],
        source_profile_item_ids=_load(row["source_profile_item_ids"], []),
        change_set=[
            ResumeVariantChange.model_validate(item) for item in _load(row["change_set"], [])
        ],
        validation_warnings=_load(row["validation_warnings"], []),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _session_from_row(row: Any) -> ApplicationLabSession:
    return ApplicationLabSession(
        session_id=row["session_id"],
        profile_id=row["profile_id"] or "",
        master_resume_id=row["master_resume_id"] or "",
        job_id=row["job_id"],
        job_snapshot_id=row["job_snapshot_id"] or "",
        current_step=row["current_step"],
        status=row["status"],
        selected_context_refs=_load(row["selected_context_refs"], []),
        analysis_run_ids=_load(row["analysis_run_ids"], []),
        readiness_report_id=row["readiness_report_id"] or "",
        resume_variant_id=row["resume_variant_id"] or "",
        application_kit_id=row["application_kit_id"] or "",
        action_plan_id=row["action_plan_id"] or "",
        tracker_application_id=row["tracker_application_id"] or "",
        invalidated_steps=_load(row["invalidated_steps"], []),
        warnings=_load(row["warnings"], []),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
    )


def _report_from_row(row: Any) -> ApplicationReadinessReport:
    return ApplicationReadinessReport(
        report_id=row["report_id"],
        session_id=row["session_id"],
        readiness_score=row["readiness_score"],
        score_explanation=row["score_explanation"],
        evidence_coverage=row["evidence_coverage"],
        requirement_coverage=row["requirement_coverage"],
        evidence_coverage_value=row["evidence_coverage_value"],
        requirement_coverage_value=row["requirement_coverage_value"],
        confidence_score=row["confidence_score"],
        risk_score=row["risk_score"],
        assessment_status=row["assessment_status"],
        unknown_dimension_count=row["unknown_dimension_count"],
        source_dimensions={
            key: ReadinessDimension.model_validate(value)
            for key, value in _load(row["source_dimensions"], {}).items()
        },
        strengths=_load(row["strengths"], []),
        top_blockers=_load(row["top_blockers"], []),
        missing_information=_load(row["missing_information"], []),
        unsupported_claim_risks=_load(row["unsupported_claim_risks"], []),
        recommended_edits=_load(row["recommended_edits"], []),
        copy_ready_snippets=_load(row["copy_ready_snippets"], []),
        action_plan_preview=_load(row["action_plan_preview"], []),
        warnings=_load(row["warnings"], []),
        provider_metadata=_load(row["provider_metadata"], {}),
        evidence_used=_load(row["evidence_used"], []),
        perspectives={
            key: ReadinessPerspective.model_validate(value)
            for key, value in _load(row["perspectives"], {}).items()
        },
        dependency_hash=row["dependency_hash"],
        stale_reason=row["stale_reason"],
        created_at=row["created_at"],
    )


def _suggestion_from_row(row: Any) -> ApplicationSuggestion:
    return ApplicationSuggestion(
        suggestion_id=row["suggestion_id"],
        session_id=row["session_id"],
        suggestion_type=row["suggestion_type"],
        section=row["section"],
        before=row["before_value"],
        after=row["after_value"],
        reason=row["reason"],
        evidence_used=_load(row["evidence_used"], []),
        source_refs=_load(row["source_refs"], []),
        warnings=_load(row["warnings"], []),
        status=row["status"],
        edited_value=row["edited_value"],
        provider_run_id=row["provider_run_id"],
        created_at=row["created_at"],
        reviewed_at=row["reviewed_at"],
    )


def _kit_item_from_row(row: Any) -> ApplicationKitItem:
    return ApplicationKitItem(
        item_id=row["item_id"],
        type=row["item_type"],
        content=row["content"],
        evidence_used=_load(row["evidence_used"], []),
        warnings=_load(row["warnings"], []),
        provider_run_id=row["provider_run_id"],
        status=row["status"],
        edited_content=row["edited_content"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _action_item_from_row(row: Any) -> ActionPlanItem:
    return ActionPlanItem(
        action_item_id=row["action_item_id"],
        title=row["title"],
        reason=row["reason"],
        priority=row["priority"],
        due_at=row["due_at"],
        related_gap=row["related_gap"],
        related_evidence=_load(row["related_evidence"], []),
        estimated_effort=row["estimated_effort"],
        status=row["status"],
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _load(value: object, default: Any) -> Any:
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _page(limit: int, offset: int) -> tuple[int, int]:
    return max(1, min(limit, 200)), max(0, offset)


__all__ = ["ApplicationLabRepository"]
