"""Typed records persisted by the local tracker."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from modules.core.collection_method import CollectionMethod
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput
from modules.tracker.status import JobStatus


def utc_now() -> datetime:
    """Return a timezone-aware timestamp."""
    return datetime.now(UTC)


class StoredAnalysis(BaseModel):
    """A privacy-conscious analysis record without raw resume content."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    job_title: str = ""
    company: str = ""
    modality: str = ""
    seniority: str = ""
    source_url: str = ""
    source_urls: list[str] = Field(default_factory=list)
    source_domains: list[str] = Field(default_factory=list)
    collection_method: CollectionMethod = "manual_url"
    requirements: list[str] = Field(default_factory=list)
    status: JobStatus = JobStatus.ANALYZED
    analysis: JobAnalysisSchema
    tailor: ResumeTailorOutput | None = None
    notes: str = ""
    privacy_acknowledged: bool = False
    job_snapshot_id: str = ""
    resume_snapshot_id: str = ""
    tailored_resume_snapshot_id: str = ""
    match_analysis_snapshot_id: str = ""
    ats_analysis_snapshot_id: str = ""
    source_capture_id: str = ""
    applied_at: datetime | None = None
    stage_history: list[dict[str, Any]] = Field(default_factory=list)
    contact_history: list[dict[str, Any]] = Field(default_factory=list)
    interview_notes: str = ""
    follow_up_at: datetime | None = None
    outcome: str = ""
    outcome_reason: str = ""
