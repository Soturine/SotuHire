"""Immutable snapshots that preserve the evidence used by career workflows."""

from __future__ import annotations

import hashlib
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


class JobSnapshot(BaseModel):
    """Immutable copy of a vacancy or opportunity at capture time."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str = Field(default_factory=lambda: uuid4().hex)
    opportunity_id: str = ""
    title: str = ""
    organization: str = ""
    location: str = ""
    description: str = ""
    source_url: str = ""
    source_refs: list[str] = Field(default_factory=list)
    captured_at: datetime = Field(default_factory=utc_now)
    content_hash: str = ""
    source_kind: str = "manual"
    raw_text: str = ""
    structured_data: dict[str, Any] = Field(default_factory=dict)


class ResumeSnapshot(BaseModel):
    """Immutable copy of the resume or variant actually used."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str = Field(default_factory=lambda: uuid4().hex)
    profile_id: str = ""
    resume_variant_id: str = ""
    title: str = "Currículo"
    content: str = ""
    structured_sections: dict[str, Any] = Field(default_factory=dict)
    source_profile_item_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    content_hash: str = ""


class AnalysisSnapshot(BaseModel):
    """Immutable analysis result and the exact evidence links used."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str = Field(default_factory=lambda: uuid4().hex)
    analysis_type: str
    job_snapshot_id: str = ""
    resume_snapshot_id: str = ""
    provider_requested: str = "local"
    provider_used: str = "local"
    model_requested: str = "local"
    model_used: str = "local"
    prompt_id: str = ""
    prompt_version: str = ""
    fallback_used: bool = False
    result: dict[str, Any] = Field(default_factory=dict)
    evidence_used: list[dict[str, Any] | str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    content_hash: str = ""


class PublicExamSnapshot(BaseModel):
    """Immutable edital and role state at review time."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str = Field(default_factory=lambda: uuid4().hex)
    notice_id: str = ""
    role_id: str = ""
    raw_text: str = ""
    structured_notice: dict[str, Any] = Field(default_factory=dict)
    requirements: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any] | str] = Field(default_factory=list)
    content_hash: str = ""
    captured_at: datetime = Field(default_factory=utc_now)


class SnapshotStore:
    """Create and retrieve immutable, content-addressed SQLite snapshots."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def create_job(self, snapshot: JobSnapshot) -> JobSnapshot:
        ensure_database(self.database_path)
        prepared = snapshot.model_copy(
            update={"content_hash": snapshot.content_hash or _snapshot_hash(snapshot)}
        )
        with connect_database(self.database_path) as connection:
            if prepared.opportunity_id:
                now = prepared.captured_at.isoformat()
                opportunity_payload = json.dumps(
                    {
                        "id": prepared.opportunity_id,
                        "title": prepared.title,
                        "organization": prepared.organization,
                        "source_url": prepared.source_url,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                connection.execute(
                    """INSERT OR IGNORE INTO opportunities
                    (id, payload, source_ref, content_hash, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        prepared.opportunity_id,
                        opportunity_payload,
                        prepared.source_url,
                        prepared.content_hash,
                        now,
                        now,
                    ),
                )
            existing = connection.execute(
                """SELECT * FROM job_snapshots
                WHERE COALESCE(opportunity_id, '') = ? AND content_hash = ?""",
                (prepared.opportunity_id, prepared.content_hash),
            ).fetchone()
            if existing is not None:
                return _job_from_row(existing)
            connection.execute(
                """INSERT INTO job_snapshots
                (snapshot_id, opportunity_id, title, organization, location, description,
                 source_url, source_refs, captured_at, content_hash, source_kind, raw_text,
                 structured_data)
                VALUES (?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prepared.snapshot_id,
                    prepared.opportunity_id,
                    prepared.title,
                    prepared.organization,
                    prepared.location,
                    prepared.description,
                    prepared.source_url,
                    _json(prepared.source_refs),
                    prepared.captured_at.isoformat(),
                    prepared.content_hash,
                    prepared.source_kind,
                    prepared.raw_text,
                    _json(prepared.structured_data),
                ),
            )
        return prepared

    def create_resume(self, snapshot: ResumeSnapshot) -> ResumeSnapshot:
        ensure_database(self.database_path)
        prepared = snapshot.model_copy(
            update={"content_hash": snapshot.content_hash or _snapshot_hash(snapshot)}
        )
        with connect_database(self.database_path) as connection:
            if prepared.profile_id:
                now = prepared.created_at.isoformat()
                connection.execute(
                    """INSERT OR IGNORE INTO profiles
                    (id, payload, source_ref, content_hash, created_at, updated_at)
                    VALUES (?, ?, '', '', ?, ?)""",
                    (prepared.profile_id, _json({"id": prepared.profile_id}), now, now),
                )
            existing = connection.execute(
                """SELECT * FROM resume_snapshots
                WHERE COALESCE(profile_id, '') = ? AND resume_variant_id = ? AND content_hash = ?""",
                (prepared.profile_id, prepared.resume_variant_id, prepared.content_hash),
            ).fetchone()
            if existing is not None:
                return _resume_from_row(existing)
            connection.execute(
                """INSERT INTO resume_snapshots
                (snapshot_id, profile_id, resume_variant_id, title, content,
                 structured_sections, source_profile_item_ids, created_at, content_hash)
                VALUES (?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prepared.snapshot_id,
                    prepared.profile_id,
                    prepared.resume_variant_id,
                    prepared.title,
                    prepared.content,
                    _json(prepared.structured_sections),
                    _json(prepared.source_profile_item_ids),
                    prepared.created_at.isoformat(),
                    prepared.content_hash,
                ),
            )
        return prepared

    def create_analysis(self, snapshot: AnalysisSnapshot) -> AnalysisSnapshot:
        ensure_database(self.database_path)
        prepared = snapshot.model_copy(
            update={"content_hash": snapshot.content_hash or _snapshot_hash(snapshot)}
        )
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                """SELECT * FROM analysis_snapshots
                WHERE analysis_type = ? AND COALESCE(job_snapshot_id, '') = ?
                AND COALESCE(resume_snapshot_id, '') = ? AND content_hash = ?""",
                (
                    prepared.analysis_type,
                    prepared.job_snapshot_id,
                    prepared.resume_snapshot_id,
                    prepared.content_hash,
                ),
            ).fetchone()
            if existing is not None:
                return _analysis_from_row(existing)
            connection.execute(
                """INSERT INTO analysis_snapshots
                (snapshot_id, analysis_type, job_snapshot_id, resume_snapshot_id,
                 provider_requested, provider_used, model_requested, model_used,
                 prompt_id, prompt_version, fallback_used, result, evidence_used,
                 source_refs, created_at, content_hash)
                VALUES (?, ?, NULLIF(?, ''), NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prepared.snapshot_id,
                    prepared.analysis_type,
                    prepared.job_snapshot_id,
                    prepared.resume_snapshot_id,
                    prepared.provider_requested,
                    prepared.provider_used,
                    prepared.model_requested,
                    prepared.model_used,
                    prepared.prompt_id,
                    prepared.prompt_version,
                    int(prepared.fallback_used),
                    _json(prepared.result),
                    _json(prepared.evidence_used),
                    _json(prepared.source_refs),
                    prepared.created_at.isoformat(),
                    prepared.content_hash,
                ),
            )
        return prepared

    def create_public_exam(self, snapshot: PublicExamSnapshot) -> PublicExamSnapshot:
        ensure_database(self.database_path)
        prepared = snapshot.model_copy(
            update={"content_hash": snapshot.content_hash or _snapshot_hash(snapshot)}
        )
        with connect_database(self.database_path) as connection:
            now = prepared.captured_at.isoformat()
            if prepared.notice_id:
                connection.execute(
                    """INSERT OR IGNORE INTO public_exam_notices
                    (id, payload, source_ref, content_hash, created_at, updated_at)
                    VALUES (?, ?, '', ?, ?, ?)""",
                    (
                        prepared.notice_id,
                        _json({"id": prepared.notice_id}),
                        prepared.content_hash,
                        now,
                        now,
                    ),
                )
            if prepared.role_id and prepared.notice_id:
                connection.execute(
                    """INSERT OR IGNORE INTO public_exam_roles
                    (id, notice_id, payload, source_ref, content_hash, created_at, updated_at)
                    VALUES (?, ?, ?, '', ?, ?, ?)""",
                    (
                        prepared.role_id,
                        prepared.notice_id,
                        _json({"id": prepared.role_id, "notice_id": prepared.notice_id}),
                        prepared.content_hash,
                        now,
                        now,
                    ),
                )
            existing = connection.execute(
                """SELECT * FROM public_exam_snapshots
                WHERE COALESCE(notice_id, '') = ? AND COALESCE(role_id, '') = ?
                AND content_hash = ?""",
                (prepared.notice_id, prepared.role_id, prepared.content_hash),
            ).fetchone()
            if existing is not None:
                return _public_exam_from_row(existing)
            connection.execute(
                """INSERT INTO public_exam_snapshots
                (snapshot_id, notice_id, role_id, raw_text, structured_notice,
                 requirements, timeline, content_hash, captured_at)
                VALUES (?, NULLIF(?, ''), NULLIF(?, ''), ?, ?, ?, ?, ?, ?)""",
                (
                    prepared.snapshot_id,
                    prepared.notice_id,
                    prepared.role_id,
                    prepared.raw_text,
                    _json(prepared.structured_notice),
                    _json(prepared.requirements),
                    _json(prepared.timeline),
                    prepared.content_hash,
                    prepared.captured_at.isoformat(),
                ),
            )
        return prepared

    def get_job(self, snapshot_id: str) -> JobSnapshot | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM job_snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone()
        return _job_from_row(row) if row is not None else None

    def get_resume(self, snapshot_id: str) -> ResumeSnapshot | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM resume_snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone()
        return _resume_from_row(row) if row is not None else None

    def get_analysis(self, snapshot_id: str) -> AnalysisSnapshot | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM analysis_snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone()
        return _analysis_from_row(row) if row is not None else None

    def get_public_exam(self, snapshot_id: str) -> PublicExamSnapshot | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM public_exam_snapshots WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone()
        return _public_exam_from_row(row) if row is not None else None


def _snapshot_hash(snapshot: BaseModel) -> str:
    payload = snapshot.model_dump(
        mode="json",
        exclude={"snapshot_id", "content_hash", "captured_at", "created_at"},
    )
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _loads(value: object, default: Any) -> Any:
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return default


def _job_from_row(row: Any) -> JobSnapshot:
    return JobSnapshot(
        snapshot_id=row["snapshot_id"],
        opportunity_id=row["opportunity_id"] or "",
        title=row["title"],
        organization=row["organization"],
        location=row["location"],
        description=row["description"],
        source_url=row["source_url"],
        source_refs=_loads(row["source_refs"], []),
        captured_at=row["captured_at"],
        content_hash=row["content_hash"],
        source_kind=row["source_kind"],
        raw_text=row["raw_text"],
        structured_data=_loads(row["structured_data"], {}),
    )


def _resume_from_row(row: Any) -> ResumeSnapshot:
    return ResumeSnapshot(
        snapshot_id=row["snapshot_id"],
        profile_id=row["profile_id"] or "",
        resume_variant_id=row["resume_variant_id"],
        title=row["title"],
        content=row["content"],
        structured_sections=_loads(row["structured_sections"], {}),
        source_profile_item_ids=_loads(row["source_profile_item_ids"], []),
        created_at=row["created_at"],
        content_hash=row["content_hash"],
    )


def _analysis_from_row(row: Any) -> AnalysisSnapshot:
    return AnalysisSnapshot(
        snapshot_id=row["snapshot_id"],
        analysis_type=row["analysis_type"],
        job_snapshot_id=row["job_snapshot_id"] or "",
        resume_snapshot_id=row["resume_snapshot_id"] or "",
        provider_requested=row["provider_requested"],
        provider_used=row["provider_used"],
        model_requested=row["model_requested"],
        model_used=row["model_used"],
        prompt_id=row["prompt_id"],
        prompt_version=row["prompt_version"],
        fallback_used=bool(row["fallback_used"]),
        result=_loads(row["result"], {}),
        evidence_used=_loads(row["evidence_used"], []),
        source_refs=_loads(row["source_refs"], []),
        created_at=row["created_at"],
        content_hash=row["content_hash"],
    )


def _public_exam_from_row(row: Any) -> PublicExamSnapshot:
    return PublicExamSnapshot(
        snapshot_id=row["snapshot_id"],
        notice_id=row["notice_id"] or "",
        role_id=row["role_id"] or "",
        raw_text=row["raw_text"],
        structured_notice=_loads(row["structured_notice"], {}),
        requirements=_loads(row["requirements"], []),
        timeline=_loads(row["timeline"], []),
        content_hash=row["content_hash"],
        captured_at=row["captured_at"],
    )
