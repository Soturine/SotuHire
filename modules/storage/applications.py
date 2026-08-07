"""SQLite application records linked to immutable snapshots."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database


def utc_now() -> datetime:
    return datetime.now(UTC)


class ApplicationRecord(BaseModel):
    """Quick or complete tracker record with optional snapshot links."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    job_snapshot_id: str = ""
    resume_snapshot_id: str = ""
    tailored_resume_snapshot_id: str = ""
    match_analysis_snapshot_id: str = ""
    ats_analysis_snapshot_id: str = ""
    source_capture_id: str = ""
    source_capture_external_reference: str = ""
    link_state: str = "not_applicable"
    job_title: str = ""
    organization: str = ""
    source_url: str = ""
    status: str = "found"
    applied_at: datetime | None = None
    stage_history: list[dict[str, Any]] = Field(default_factory=list)
    contact_history: list[dict[str, Any]] = Field(default_factory=list)
    interview_notes: str = ""
    follow_up_at: datetime | None = None
    outcome: str = ""
    outcome_reason: str = ""
    application_lab_session_id: str = ""
    readiness_report_id: str = ""
    resume_variant_id: str = ""
    application_kit_id: str = ""
    action_plan_id: str = ""
    lab_analysis_snapshot_id: str = ""
    readiness_analysis_snapshot_id: str = ""
    tailor_analysis_snapshot_id: str = ""
    analysis_bundle_id: str = ""
    application_kit_snapshot_id: str = ""
    dependency_hash: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ApplicationRepository:
    """Persist application links and append stage events transactionally."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def save(self, record: ApplicationRecord) -> ApplicationRecord:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            return _save_record(connection, record)

    def get(self, application_id: str) -> ApplicationRecord | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM applications WHERE id = ?", (application_id,)
            ).fetchone()
        return _from_row(row) if row is not None else None

    def list(self, *, limit: int = 500, offset: int = 0) -> list[ApplicationRecord]:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """SELECT * FROM applications ORDER BY updated_at DESC
                LIMIT ? OFFSET ?""",
                (max(1, min(limit, 2000)), max(0, offset)),
            ).fetchall()
        return [_from_row(row) for row in rows]

    def complete_lab_transaction(
        self,
        record: ApplicationRecord,
        *,
        session_id: str,
        idempotency_key: str,
    ) -> ApplicationRecord:
        """Atomically create a card, its initial outcome and Lab completion."""
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT result_ref FROM idempotency_records WHERE operation_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                row = connection.execute(
                    "SELECT * FROM applications WHERE id = ?", (existing["result_ref"],)
                ).fetchone()
                if row is None:
                    raise RuntimeError("Registro idempotente sem candidatura vinculada.")
                return _from_row(row)

            saved = _save_record(connection, record)
            connection.execute(
                """INSERT INTO outcome_events
                (event_id, application_id, event_type, occurred_at, source,
                 resume_variant_id, match_score, ats_score, metadata, created_at)
                VALUES (?, ?, 'application_created', ?, 'application_lab', ?, ?, ?, '{}', ?)""",
                (
                    uuid4().hex,
                    saved.id,
                    saved.updated_at.isoformat(),
                    saved.resume_variant_id,
                    _nested_score(saved.payload, "match_score"),
                    _nested_score(saved.payload, "ats_score"),
                    saved.updated_at.isoformat(),
                ),
            )
            completed_at = saved.updated_at.isoformat()
            cursor = connection.execute(
                """UPDATE application_lab_sessions
                SET tracker_application_id = ?, status = 'completed', current_step = 10,
                    completed_at = ?, updated_at = ?
                WHERE session_id = ?""",
                (saved.id, completed_at, completed_at, session_id),
            )
            if cursor.rowcount != 1:
                raise LookupError("Sessão do Application Lab não encontrada.")
            connection.execute(
                """INSERT INTO idempotency_records
                (operation_key, operation_type, result_ref, result_hash, created_at)
                VALUES (?, 'application_lab_tracker_save', ?, ?, ?)""",
                (
                    idempotency_key,
                    saved.id,
                    saved.dependency_hash,
                    completed_at,
                ),
            )
        return saved


def _save_record(connection: sqlite3.Connection, record: ApplicationRecord) -> ApplicationRecord:
    requested_capture = record.source_capture_id or record.source_capture_external_reference
    capture_exists = bool(
        requested_capture
        and connection.execute(
            "SELECT 1 FROM captures WHERE id = ?", (requested_capture,)
        ).fetchone()
    )
    prepared = record.model_copy(
        update={
            "source_capture_id": requested_capture if capture_exists else "",
            "source_capture_external_reference": "" if capture_exists else requested_capture,
            "link_state": (
                "linked"
                if capture_exists
                else "pending_link"
                if requested_capture
                else "not_applicable"
            ),
        }
    )
    current = connection.execute(
        "SELECT status FROM applications WHERE id = ?", (prepared.id,)
    ).fetchone()
    parameters = {
        **prepared.model_dump(mode="json"),
        "applied_at": prepared.applied_at.isoformat() if prepared.applied_at else None,
        "stage_history": _json(prepared.stage_history),
        "contact_history": _json(prepared.contact_history),
        "follow_up_at": (prepared.follow_up_at.isoformat() if prepared.follow_up_at else None),
        "payload": _json(prepared.payload),
        "created_at": prepared.created_at.isoformat(),
        "updated_at": prepared.updated_at.isoformat(),
    }
    connection.execute(
        """INSERT INTO applications
        (id, job_snapshot_id, resume_snapshot_id, tailored_resume_snapshot_id,
         match_analysis_snapshot_id, ats_analysis_snapshot_id, source_capture_id,
         source_capture_external_reference, link_state, job_title, organization, source_url,
         status, applied_at, stage_history, contact_history, interview_notes, follow_up_at,
         outcome, outcome_reason, application_lab_session_id, readiness_report_id,
         resume_variant_id, application_kit_id, action_plan_id, lab_analysis_snapshot_id,
         readiness_analysis_snapshot_id, tailor_analysis_snapshot_id, analysis_bundle_id,
         application_kit_snapshot_id, dependency_hash, payload, created_at, updated_at)
        VALUES (:id, NULLIF(:job_snapshot_id, ''), NULLIF(:resume_snapshot_id, ''),
                NULLIF(:tailored_resume_snapshot_id, ''),
                NULLIF(:match_analysis_snapshot_id, ''),
                NULLIF(:ats_analysis_snapshot_id, ''), NULLIF(:source_capture_id, ''),
                :source_capture_external_reference, :link_state, :job_title, :organization,
                :source_url, :status, :applied_at, :stage_history, :contact_history,
                :interview_notes, :follow_up_at, :outcome, :outcome_reason,
                NULLIF(:application_lab_session_id, ''), NULLIF(:readiness_report_id, ''),
                NULLIF(:resume_variant_id, ''), NULLIF(:application_kit_id, ''),
                NULLIF(:action_plan_id, ''), NULLIF(:lab_analysis_snapshot_id, ''),
                NULLIF(:readiness_analysis_snapshot_id, ''),
                NULLIF(:tailor_analysis_snapshot_id, ''), NULLIF(:analysis_bundle_id, ''),
                NULLIF(:application_kit_snapshot_id, ''), :dependency_hash, :payload,
                :created_at, :updated_at)
        ON CONFLICT(id) DO UPDATE SET
            job_snapshot_id=excluded.job_snapshot_id,
            resume_snapshot_id=excluded.resume_snapshot_id,
            tailored_resume_snapshot_id=excluded.tailored_resume_snapshot_id,
            match_analysis_snapshot_id=excluded.match_analysis_snapshot_id,
            ats_analysis_snapshot_id=excluded.ats_analysis_snapshot_id,
            source_capture_id=excluded.source_capture_id,
            source_capture_external_reference=excluded.source_capture_external_reference,
            link_state=excluded.link_state,
            job_title=excluded.job_title,
            organization=excluded.organization,
            source_url=excluded.source_url,
            status=excluded.status,
            applied_at=excluded.applied_at,
            stage_history=excluded.stage_history,
            contact_history=excluded.contact_history,
            interview_notes=excluded.interview_notes,
            follow_up_at=excluded.follow_up_at,
            outcome=excluded.outcome,
            outcome_reason=excluded.outcome_reason,
            application_lab_session_id=excluded.application_lab_session_id,
            readiness_report_id=excluded.readiness_report_id,
            resume_variant_id=excluded.resume_variant_id,
            application_kit_id=excluded.application_kit_id,
            action_plan_id=excluded.action_plan_id,
            lab_analysis_snapshot_id=excluded.lab_analysis_snapshot_id,
            readiness_analysis_snapshot_id=excluded.readiness_analysis_snapshot_id,
            tailor_analysis_snapshot_id=excluded.tailor_analysis_snapshot_id,
            analysis_bundle_id=excluded.analysis_bundle_id,
            application_kit_snapshot_id=excluded.application_kit_snapshot_id,
            dependency_hash=excluded.dependency_hash,
            payload=excluded.payload,
            updated_at=excluded.updated_at""",
        parameters,
    )
    if current is None or str(current["status"]) != prepared.status:
        connection.execute(
            """INSERT INTO application_events
            (id, application_id, event_type, event_at, payload, created_at, updated_at)
            VALUES (?, ?, 'stage_changed', ?, ?, ?, ?)""",
            (
                uuid4().hex,
                prepared.id,
                prepared.updated_at.isoformat(),
                _json({"status": prepared.status}),
                prepared.updated_at.isoformat(),
                prepared.updated_at.isoformat(),
            ),
        )
    return prepared


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _load(value: object, default: Any) -> Any:
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return default


def _nested_score(payload: dict[str, Any], name: str) -> float | None:
    lab = payload.get("application_lab", {})
    value = lab.get(name) if isinstance(lab, dict) else None
    return float(value) if isinstance(value, int | float) else None


def _row_value(row: Any, key: str, default: Any = "") -> Any:
    """Read columns added by explicit migrations without mutating legacy databases."""
    try:
        return row[key]
    except (IndexError, KeyError):
        return default


def _from_row(row: Any) -> ApplicationRecord:
    return ApplicationRecord(
        id=_row_value(row, "id"),
        job_snapshot_id=_row_value(row, "job_snapshot_id") or "",
        resume_snapshot_id=_row_value(row, "resume_snapshot_id") or "",
        tailored_resume_snapshot_id=_row_value(row, "tailored_resume_snapshot_id") or "",
        match_analysis_snapshot_id=_row_value(row, "match_analysis_snapshot_id") or "",
        ats_analysis_snapshot_id=_row_value(row, "ats_analysis_snapshot_id") or "",
        source_capture_id=_row_value(row, "source_capture_id") or "",
        source_capture_external_reference=_row_value(row, "source_capture_external_reference")
        or "",
        link_state=_row_value(row, "link_state", "not_applicable"),
        job_title=_row_value(row, "job_title"),
        organization=_row_value(row, "organization"),
        source_url=_row_value(row, "source_url"),
        status=_row_value(row, "status", "found"),
        applied_at=_row_value(row, "applied_at", None),
        stage_history=_load(_row_value(row, "stage_history", "[]"), []),
        contact_history=_load(_row_value(row, "contact_history", "[]"), []),
        interview_notes=_row_value(row, "interview_notes"),
        follow_up_at=_row_value(row, "follow_up_at", None),
        outcome=_row_value(row, "outcome"),
        outcome_reason=_row_value(row, "outcome_reason"),
        application_lab_session_id=_row_value(row, "application_lab_session_id") or "",
        readiness_report_id=_row_value(row, "readiness_report_id") or "",
        resume_variant_id=_row_value(row, "resume_variant_id") or "",
        application_kit_id=_row_value(row, "application_kit_id") or "",
        action_plan_id=_row_value(row, "action_plan_id") or "",
        lab_analysis_snapshot_id=_row_value(row, "lab_analysis_snapshot_id") or "",
        readiness_analysis_snapshot_id=_row_value(row, "readiness_analysis_snapshot_id") or "",
        tailor_analysis_snapshot_id=_row_value(row, "tailor_analysis_snapshot_id") or "",
        analysis_bundle_id=_row_value(row, "analysis_bundle_id") or "",
        application_kit_snapshot_id=_row_value(row, "application_kit_snapshot_id") or "",
        dependency_hash=_row_value(row, "dependency_hash"),
        payload=_load(_row_value(row, "payload", "{}"), {}),
        created_at=_row_value(row, "created_at", utc_now()),
        updated_at=_row_value(row, "updated_at", utc_now()),
    )


__all__ = ["ApplicationRecord", "ApplicationRepository"]
