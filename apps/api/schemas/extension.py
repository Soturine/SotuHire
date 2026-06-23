"""DTOs for the web frontend bridge to the local browser companion."""

from __future__ import annotations

from datetime import datetime

from modules.portfolio.schemas import ProjectAnalysisReport
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
    status: str = "captured"
    tracker_id: str = ""
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
