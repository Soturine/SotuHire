"""DTOs for source collection endpoints."""

from __future__ import annotations

from modules.schemas.job_posting import JobPostingSchema
from modules.scraping.browser_session import DEFAULT_CDP_URL
from modules.sources.imports import (
    CaptureStatus,
    DuplicateCandidate,
    ImportBatch,
    JobSourceDirectory,
    OpportunityInboxItem,
    SourceExportFormat,
)
from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedBrowserStatusResponse(BaseModel):
    """Status of the local Chromium CDP session."""

    model_config = ConfigDict(extra="forbid")

    available: bool
    endpoint: str = DEFAULT_CDP_URL
    browser: str = ""
    message: str = ""


class AuthenticatedBrowserLaunchRequest(BaseModel):
    """Request to open the dedicated browser for manual login."""

    model_config = ConfigDict(extra="forbid")

    start_url: str = Field(default="https://www.linkedin.com/jobs/", max_length=2048)
    browser_cdp_url: str = Field(default=DEFAULT_CDP_URL, max_length=200)
    request_id: str = Field(default="", max_length=120)


class AuthenticatedBrowserCollectRequest(BaseModel):
    """Request to collect from an already-authenticated authorized browser."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="LinkedIn autorizado", min_length=1, max_length=200)
    url: str = Field(default="https://www.linkedin.com/jobs/", max_length=2048)
    browser_cdp_url: str = Field(default=DEFAULT_CDP_URL, max_length=200)
    max_items: int = Field(default=20, ge=1, le=100)
    max_pages: int = Field(default=3, ge=1, le=20)
    delay_seconds: float = Field(default=2.0, ge=0.2, le=60)
    authorized_use: bool = False
    authorization_reference: str = Field(default="", max_length=500)
    request_id: str = Field(default="", max_length=120)


class AuthenticatedBrowserOpportunityItem(BaseModel):
    """Small public summary of a collected opportunity."""

    model_config = ConfigDict(extra="forbid")

    title: str
    company: str = ""
    source_url: str = ""
    confidence: float = Field(ge=0, le=1)


class AuthenticatedBrowserCollectResponse(BaseModel):
    """Result of an authenticated browser collection run."""

    model_config = ConfigDict(extra="forbid")

    new_count: int = 0
    duplicate_count: int = 0
    updated_count: int = 0
    failures: list[str] = Field(default_factory=list)
    opportunities: list[AuthenticatedBrowserOpportunityItem] = Field(default_factory=list)


class SourceImportTextRequest(BaseModel):
    """Import one pasted job description into the local opportunity inbox."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=200_000)
    url: str = Field(default="", max_length=2048)
    company: str = Field(default="", max_length=200)
    title: str = Field(default="", max_length=300)
    source_name: str = Field(default="Texto manual", max_length=120)
    notes: str = Field(default="", max_length=10_000)
    use_ai: bool = False
    request_id: str = Field(default="", max_length=120)


class SourceImportUrlRequest(BaseModel):
    """Import one public URL when safe simple reading is possible."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1, max_length=2048)
    source_name: str = Field(default="Link manual", max_length=120)
    notes: str = Field(default="", max_length=10_000)
    use_ai: bool = False
    request_id: str = Field(default="", max_length=120)


class SourceImportCsvRequest(BaseModel):
    """Import opportunities from CSV text."""

    model_config = ConfigDict(extra="forbid")

    csv_text: str = Field(min_length=1, max_length=1_000_000)
    source_name: str = Field(default="CSV Manual", max_length=120)
    use_ai: bool = False
    request_id: str = Field(default="", max_length=120)


class SourceImportJsonRequest(BaseModel):
    """Import opportunities from JSON rows or JSON text."""

    model_config = ConfigDict(extra="forbid")

    items: list[dict[str, object]] = Field(default_factory=list, max_length=500)
    json_text: str = Field(default="", max_length=1_000_000)
    source_name: str = Field(default="JSON Manual", max_length=120)
    use_ai: bool = False
    request_id: str = Field(default="", max_length=120)


class SourceCapturePatchRequest(BaseModel):
    """Update one capture/inbox item."""

    model_config = ConfigDict(extra="forbid")

    status: CaptureStatus | None = None
    notes: str | None = Field(default=None, max_length=10_000)
    duplicate_of: str | None = Field(default=None, max_length=120)
    request_id: str = Field(default="", max_length=120)


class SourceCaptureMergeRequest(BaseModel):
    """Merge one duplicate into an existing inbox record without deleting history."""

    model_config = ConfigDict(extra="forbid")

    duplicate_of: str = Field(min_length=1, max_length=120)
    notes: str = Field(default="", max_length=10_000)
    request_id: str = Field(default="", max_length=120)


class SourceExportRequest(BaseModel):
    """Export inbox items to local CSV or JSON content."""

    model_config = ConfigDict(extra="forbid")

    format: SourceExportFormat = "csv"
    item_ids: list[str] = Field(default_factory=list, max_length=500)
    request_id: str = Field(default="", max_length=120)


class SourceImportsResponse(BaseModel):
    """Opportunity inbox plus recent import batches."""

    model_config = ConfigDict(extra="forbid")

    items: list[OpportunityInboxItem] = Field(default_factory=list)
    batches: list[ImportBatch] = Field(default_factory=list)


class SourceImportResponse(BaseModel):
    """Result of one import action."""

    model_config = ConfigDict(extra="forbid")

    batch: ImportBatch
    items: list[OpportunityInboxItem] = Field(default_factory=list)
    message: str = ""


class SourceCapturesResponse(BaseModel):
    """Persistent captures/inbox records."""

    model_config = ConfigDict(extra="forbid")

    captures: list[OpportunityInboxItem] = Field(default_factory=list)


class SourceCaptureResponse(BaseModel):
    """One updated capture/inbox item."""

    model_config = ConfigDict(extra="forbid")

    capture: OpportunityInboxItem
    message: str = ""


class SourceCaptureImportJobResponse(BaseModel):
    """Capture parsed as a job for the Vaga flow."""

    model_config = ConfigDict(extra="forbid")

    capture: OpportunityInboxItem
    job: JobPostingSchema
    message: str = ""


class SourceCaptureSaveTrackerResponse(BaseModel):
    """Capture saved into tracker."""

    model_config = ConfigDict(extra="forbid")

    capture: OpportunityInboxItem
    tracker_id: str
    message: str = ""


class SourceDedupeResponse(BaseModel):
    """Duplicate candidates detected by local dedupe."""

    model_config = ConfigDict(extra="forbid")

    duplicates: list[DuplicateCandidate] = Field(default_factory=list)


class SourceDirectoryResponse(BaseModel):
    """Safe public/offical source directory entries."""

    model_config = ConfigDict(extra="forbid")

    sources: list[JobSourceDirectory] = Field(default_factory=list)
    query: str = ""
    warnings: list[str] = Field(default_factory=list)


class SourceExportResponse(BaseModel):
    """Local export payload."""

    model_config = ConfigDict(extra="forbid")

    format: SourceExportFormat
    filename: str
    content: str
    item_count: int


class SourceStatsResponse(BaseModel):
    """Compact source import stats."""

    model_config = ConfigDict(extra="forbid")

    total: int = 0
    duplicates: int = 0
    errors: int = 0
    saved_to_tracker: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_origin: dict[str, int] = Field(default_factory=dict)
