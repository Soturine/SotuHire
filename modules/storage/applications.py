"""SQLite application records linked to immutable snapshots."""

from __future__ import annotations

import json
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
            if record.source_capture_id:
                now = record.updated_at.isoformat()
                connection.execute(
                    """INSERT OR IGNORE INTO captures
                    (id, payload, source_ref, content_hash, created_at, updated_at)
                    VALUES (?, ?, '', '', ?, ?)""",
                    (
                        record.source_capture_id,
                        _json({"id": record.source_capture_id, "placeholder": True}),
                        now,
                        now,
                    ),
                )
            current = connection.execute(
                "SELECT status FROM applications WHERE id = ?", (record.id,)
            ).fetchone()
            connection.execute(
                """INSERT INTO applications
                (id, job_snapshot_id, resume_snapshot_id, tailored_resume_snapshot_id,
                 match_analysis_snapshot_id, ats_analysis_snapshot_id, source_capture_id,
                 job_title, organization, source_url, status, applied_at, stage_history,
                 contact_history, interview_notes, follow_up_at, outcome, outcome_reason,
                 payload, created_at, updated_at)
                VALUES (?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''),
                        NULLIF(?, ''), NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    job_snapshot_id=excluded.job_snapshot_id,
                    resume_snapshot_id=excluded.resume_snapshot_id,
                    tailored_resume_snapshot_id=excluded.tailored_resume_snapshot_id,
                    match_analysis_snapshot_id=excluded.match_analysis_snapshot_id,
                    ats_analysis_snapshot_id=excluded.ats_analysis_snapshot_id,
                    source_capture_id=excluded.source_capture_id,
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
                    payload=excluded.payload,
                    updated_at=excluded.updated_at""",
                (
                    record.id,
                    record.job_snapshot_id,
                    record.resume_snapshot_id,
                    record.tailored_resume_snapshot_id,
                    record.match_analysis_snapshot_id,
                    record.ats_analysis_snapshot_id,
                    record.source_capture_id,
                    record.job_title,
                    record.organization,
                    record.source_url,
                    record.status,
                    record.applied_at.isoformat() if record.applied_at else None,
                    _json(record.stage_history),
                    _json(record.contact_history),
                    record.interview_notes,
                    record.follow_up_at.isoformat() if record.follow_up_at else None,
                    record.outcome,
                    record.outcome_reason,
                    _json(record.payload),
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                ),
            )
            if current is None or str(current["status"]) != record.status:
                connection.execute(
                    """INSERT INTO application_events
                    (id, application_id, event_type, event_at, payload, created_at, updated_at)
                    VALUES (?, ?, 'stage_changed', ?, ?, ?, ?)""",
                    (
                        uuid4().hex,
                        record.id,
                        record.updated_at.isoformat(),
                        _json({"status": record.status}),
                        record.updated_at.isoformat(),
                        record.updated_at.isoformat(),
                    ),
                )
        return record

    def get(self, application_id: str) -> ApplicationRecord | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM applications WHERE id = ?", (application_id,)
            ).fetchone()
        return _from_row(row) if row is not None else None


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _load(value: object, default: Any) -> Any:
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return default


def _from_row(row: Any) -> ApplicationRecord:
    return ApplicationRecord(
        id=row["id"],
        job_snapshot_id=row["job_snapshot_id"] or "",
        resume_snapshot_id=row["resume_snapshot_id"] or "",
        tailored_resume_snapshot_id=row["tailored_resume_snapshot_id"] or "",
        match_analysis_snapshot_id=row["match_analysis_snapshot_id"] or "",
        ats_analysis_snapshot_id=row["ats_analysis_snapshot_id"] or "",
        source_capture_id=row["source_capture_id"] or "",
        job_title=row["job_title"],
        organization=row["organization"],
        source_url=row["source_url"],
        status=row["status"],
        applied_at=row["applied_at"],
        stage_history=_load(row["stage_history"], []),
        contact_history=_load(row["contact_history"], []),
        interview_notes=row["interview_notes"],
        follow_up_at=row["follow_up_at"],
        outcome=row["outcome"],
        outcome_reason=row["outcome_reason"],
        payload=_load(row["payload"], {}),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
