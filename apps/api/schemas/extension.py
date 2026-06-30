"""DTOs for the web frontend bridge to the local browser companion."""

from __future__ import annotations

from datetime import datetime

from modules.context import CareerContext
from modules.portfolio.schemas import ProjectAnalysisReport
from modules.profile.models import ProfileItem
from modules.schemas.job_posting import JobPostingSchema
from pydantic import BaseModel, ConfigDict, Field


class ExtensionStatusResponse(BaseModel):
    """Safe status for the local extension/companion bridge."""

    model_config = ConfigDict(extra="forbid")

    available: bool = True
    companion_url: str = "http://127.0.0.1:8765"
    capture_count: int = 0
    last_capture_at: datetime | None = None
    message: str = ""


class ExtensionCaptureItem(BaseModel):
    """Small capture summary safe for the web frontend."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str = ""
    company: str = ""
    url: str = ""
    domain: str = ""
    kind: str = "other"
    source: str = "browser_assisted_capture"
    status: str = "captured"
    tracker_id: str = ""
    profile_candidate_count: int = 0
    context_signal: str = ""
    captured_at: datetime | None = None
    updated_at: datetime | None = None


class ExtensionCapturesResponse(BaseModel):
    """Recent local extension captures."""

    model_config = ConfigDict(extra="forbid")

    captures: list[ExtensionCaptureItem] = Field(default_factory=list)


class ExtensionImportRequest(BaseModel):
    """Action request for a previously captured item."""

    model_config = ConfigDict(extra="forbid")

    capture_id: str = Field(min_length=1, max_length=120)
    use_ai: bool = False
    privacy_acknowledged: bool = True
    request_id: str = Field(default="", max_length=120)


class ExtensionCapturePatchRequest(BaseModel):
    """Safe user status update for a local companion capture."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(default="reviewed", max_length=80)
    request_id: str = Field(default="", max_length=120)


class ExtensionCapturePatchResponse(BaseModel):
    """Updated local companion capture."""

    model_config = ConfigDict(extra="forbid")

    capture: ExtensionCaptureItem
    message: str = ""


class ExtensionImportJobResponse(BaseModel):
    """Parsed job imported from a local extension capture."""

    model_config = ConfigDict(extra="forbid")

    capture_id: str
    job: JobPostingSchema
    message: str


class ExtensionImportTrackerResponse(BaseModel):
    """Tracker import result for a local extension capture."""

    model_config = ConfigDict(extra="forbid")

    capture_id: str
    tracker_id: str = ""
    message: str
    provider: str = "local"


class ExtensionImportGithubResponse(BaseModel):
    """Project/GitHub import result for a local extension capture."""

    model_config = ConfigDict(extra="forbid")

    capture_id: str
    report: ProjectAnalysisReport
    message: str


class ExtensionContextResponse(BaseModel):
    """Unified context visible to the extension bridge."""

    model_config = ConfigDict(extra="forbid")

    context: CareerContext
    context_summary: str = ""
    message: str = ""


class ExtensionProfileCandidatesRequest(BaseModel):
    """Reviewed selection to promote extension candidates into the profile."""

    model_config = ConfigDict(extra="forbid")

    candidate_ids: list[str] = Field(default_factory=list, max_length=50)
    items: list[ProfileItem] = Field(default_factory=list, max_length=50)
    privacy_acknowledged: bool = True
    request_id: str = Field(default="", max_length=120)


class ExtensionProfileCandidatesResponse(BaseModel):
    """Review-only profile item candidates derived from one extension source."""

    model_config = ConfigDict(extra="forbid")

    capture_id: str = ""
    project_id: str = ""
    candidates: list[ProfileItem] = Field(default_factory=list)
    context_summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    message: str = ""


class ExtensionAddToProfileResponse(BaseModel):
    """Items explicitly confirmed by the user and added to the profile."""

    model_config = ConfigDict(extra="forbid")

    capture_id: str = ""
    project_id: str = ""
    added: list[ProfileItem] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    message: str = ""
