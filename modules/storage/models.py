"""Typed records persisted by the local tracker."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

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
    status: JobStatus = JobStatus.ANALYZED
    analysis: JobAnalysisSchema
    tailor: ResumeTailorOutput | None = None
    notes: str = ""
    privacy_acknowledged: bool = False
