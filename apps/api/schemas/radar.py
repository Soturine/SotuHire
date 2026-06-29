"""DTOs for Job Radar API endpoints."""

from __future__ import annotations

from modules.ai.schemas.analysis_insights import WishlistDraftOutput
from modules.radar.models import (
    JobWishlist,
    RadarAlert,
    RadarAlertStatus,
    RadarResult,
    RadarResultStatus,
    RadarRun,
    RadarSource,
    RadarSourceStatus,
    RadarSourceType,
    RadarStats,
    SourceAdapter,
)
from modules.radar.schedule_models import (
    LocalNotification,
    RadarSchedule,
    RadarScheduledRun,
    RadarSchedulerStatus,
    ScheduleFrequency,
)
from modules.sources.imports import OpportunityInboxItem
from pydantic import BaseModel, ConfigDict, Field


class RadarWishlistRequest(BaseModel):
    """Create or update a Job Radar wishlist."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="Wishlist principal", max_length=160)
    target_titles: list[str] = Field(default_factory=list, max_length=40)
    target_domains: list[str] = Field(default_factory=list, max_length=40)
    target_seniority: list[str] = Field(default_factory=list, max_length=20)
    required_skills: list[str] = Field(default_factory=list, max_length=80)
    desired_skills: list[str] = Field(default_factory=list, max_length=80)
    excluded_terms: list[str] = Field(default_factory=list, max_length=80)
    locations: list[str] = Field(default_factory=list, max_length=40)
    remote_preferences: list[str] = Field(default_factory=list, max_length=20)
    work_model: str = Field(default="", max_length=80)
    employment_type: str = Field(default="", max_length=80)
    salary_min: int | None = Field(default=None, ge=0)
    salary_currency: str = Field(default="BRL", max_length=12)
    contract_types: list[str] = Field(default_factory=list, max_length=30)
    industries: list[str] = Field(default_factory=list, max_length=40)
    companies_include: list[str] = Field(default_factory=list, max_length=60)
    companies_exclude: list[str] = Field(default_factory=list, max_length=60)
    source_types: list[str] = Field(default_factory=list, max_length=20)
    min_match_score: int = Field(default=70, ge=0, le=100)
    min_ats_score: int = Field(default=0, ge=0, le=100)
    notify_on_new_matches: bool = True
    notes: str = Field(default="", max_length=10_000)
    is_active: bool = True
    request_id: str = Field(default="", max_length=120)


class RadarWishlistPatchRequest(BaseModel):
    """Patch shape for wishlists."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=160)
    target_titles: list[str] | None = Field(default=None, max_length=40)
    target_domains: list[str] | None = Field(default=None, max_length=40)
    target_seniority: list[str] | None = Field(default=None, max_length=20)
    required_skills: list[str] | None = Field(default=None, max_length=80)
    desired_skills: list[str] | None = Field(default=None, max_length=80)
    excluded_terms: list[str] | None = Field(default=None, max_length=80)
    locations: list[str] | None = Field(default=None, max_length=40)
    remote_preferences: list[str] | None = Field(default=None, max_length=20)
    work_model: str | None = Field(default=None, max_length=80)
    employment_type: str | None = Field(default=None, max_length=80)
    salary_min: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, max_length=12)
    contract_types: list[str] | None = Field(default=None, max_length=30)
    industries: list[str] | None = Field(default=None, max_length=40)
    companies_include: list[str] | None = Field(default=None, max_length=60)
    companies_exclude: list[str] | None = Field(default=None, max_length=60)
    source_types: list[str] | None = Field(default=None, max_length=20)
    min_match_score: int | None = Field(default=None, ge=0, le=100)
    min_ats_score: int | None = Field(default=None, ge=0, le=100)
    notify_on_new_matches: bool | None = None
    notes: str | None = Field(default=None, max_length=10_000)
    is_active: bool | None = None
    request_id: str = Field(default="", max_length=120)


class RadarWishlistDraftRequest(BaseModel):
    """Free-text request for an unsaved wishlist draft."""

    model_config = ConfigDict(extra="forbid")

    free_text: str = Field(min_length=1, max_length=5_000)
    use_profile_context: bool = True
    language: str = Field(default="pt-BR", max_length=20)
    profile_context_override: dict[str, object] | None = None
    request_id: str = Field(default="", max_length=120)


class RadarWishlistDraftResponse(WishlistDraftOutput):
    """Validated unsaved wishlist draft response."""


class RadarSourceRequest(BaseModel):
    """Create one radar source."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    source_type: RadarSourceType = "public_feed"
    url: str = Field(default="", max_length=2048)
    docs_url: str = Field(default="", max_length=2048)
    status: RadarSourceStatus = "available"
    is_active: bool = True
    requires_api_key: bool = False
    max_results: int = Field(default=20, ge=1, le=100)
    timeout_seconds: float = Field(default=6.0, ge=1.0, le=30.0)
    rate_limit_seconds: float = Field(default=1.0, ge=0.2, le=60.0)
    notes: str = Field(default="", max_length=10_000)
    metadata: dict[str, object] = Field(default_factory=dict)
    request_id: str = Field(default="", max_length=120)


class RadarSourcePatchRequest(BaseModel):
    """Patch one radar source."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=160)
    source_type: RadarSourceType | None = None
    url: str | None = Field(default=None, max_length=2048)
    docs_url: str | None = Field(default=None, max_length=2048)
    status: RadarSourceStatus | None = None
    is_active: bool | None = None
    requires_api_key: bool | None = None
    max_results: int | None = Field(default=None, ge=1, le=100)
    timeout_seconds: float | None = Field(default=None, ge=1.0, le=30.0)
    rate_limit_seconds: float | None = Field(default=None, ge=0.2, le=60.0)
    notes: str | None = Field(default=None, max_length=10_000)
    metadata: dict[str, object] | None = None
    request_id: str = Field(default="", max_length=120)


class RadarRunRequest(BaseModel):
    """Manual radar run request."""

    model_config = ConfigDict(extra="forbid")

    source_ids: list[str] = Field(default_factory=list, max_length=20)
    wishlist_id: str = Field(default="", max_length=120)
    resume_text: str = Field(default="", max_length=200_000)
    keywords: list[str] = Field(default_factory=list, max_length=40)
    use_ai: bool = False
    request_id: str = Field(default="", max_length=120)


class RadarScheduleRequest(BaseModel):
    """Create one local Radar schedule."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="Radar agendado", min_length=1, max_length=160)
    enabled: bool = True
    wishlist_id: str | None = Field(default=None, max_length=120)
    source_ids: list[str] = Field(default_factory=list, max_length=50)
    keywords: list[str] = Field(default_factory=list, max_length=40)
    use_ai: bool = False
    use_profile_context: bool = True
    frequency: ScheduleFrequency = "daily"
    interval_minutes: int | None = Field(default=None, ge=60, le=10_080)
    timezone: str = Field(default="local", max_length=80)
    quiet_hours_start: str | None = Field(default=None, max_length=5)
    quiet_hours_end: str | None = Field(default=None, max_length=5)
    cooldown_minutes: int = Field(default=720, ge=0, le=43_200)
    min_match_score: int | None = Field(default=None, ge=0, le=100)
    min_ats_score: int | None = Field(default=None, ge=0, le=100)
    notify_on_new_matches: bool = True
    notify_on_score_threshold: bool = True
    request_id: str = Field(default="", max_length=120)


class RadarSchedulePatchRequest(BaseModel):
    """Patch one local Radar schedule."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=160)
    enabled: bool | None = None
    wishlist_id: str | None = Field(default=None, max_length=120)
    source_ids: list[str] | None = Field(default=None, max_length=50)
    keywords: list[str] | None = Field(default=None, max_length=40)
    use_ai: bool | None = None
    use_profile_context: bool | None = None
    frequency: ScheduleFrequency | None = None
    interval_minutes: int | None = Field(default=None, ge=60, le=10_080)
    timezone: str | None = Field(default=None, max_length=80)
    quiet_hours_start: str | None = Field(default=None, max_length=5)
    quiet_hours_end: str | None = Field(default=None, max_length=5)
    cooldown_minutes: int | None = Field(default=None, ge=0, le=43_200)
    min_match_score: int | None = Field(default=None, ge=0, le=100)
    min_ats_score: int | None = Field(default=None, ge=0, le=100)
    notify_on_new_matches: bool | None = None
    notify_on_score_threshold: bool | None = None
    request_id: str = Field(default="", max_length=120)


class RadarResultPatchRequest(BaseModel):
    """Patch one radar result."""

    model_config = ConfigDict(extra="forbid")

    status: RadarResultStatus | None = None
    request_id: str = Field(default="", max_length=120)


class RadarAlertPatchRequest(BaseModel):
    """Patch one radar alert."""

    model_config = ConfigDict(extra="forbid")

    status: RadarAlertStatus | None = None
    request_id: str = Field(default="", max_length=120)


class RadarWishlistsResponse(BaseModel):
    """Wishlist list response."""

    model_config = ConfigDict(extra="forbid")

    wishlists: list[JobWishlist] = Field(default_factory=list)


class RadarWishlistResponse(BaseModel):
    """One wishlist response."""

    model_config = ConfigDict(extra="forbid")

    wishlist: JobWishlist
    message: str = ""


class RadarSourcesResponse(BaseModel):
    """Radar sources response."""

    model_config = ConfigDict(extra="forbid")

    sources: list[RadarSource] = Field(default_factory=list)
    adapters: list[SourceAdapter] = Field(default_factory=list)


class RadarSourceResponse(BaseModel):
    """One source response."""

    model_config = ConfigDict(extra="forbid")

    source: RadarSource
    message: str = ""


class RadarRunResponse(BaseModel):
    """Result of one manual radar run."""

    model_config = ConfigDict(extra="forbid")

    run: RadarRun
    results: list[RadarResult] = Field(default_factory=list)
    alerts: list[RadarAlert] = Field(default_factory=list)
    message: str = ""


class RadarRunsResponse(BaseModel):
    """Run history response."""

    model_config = ConfigDict(extra="forbid")

    runs: list[RadarRun] = Field(default_factory=list)


class RadarSchedulesResponse(BaseModel):
    """Schedule list response."""

    model_config = ConfigDict(extra="forbid")

    schedules: list[RadarSchedule] = Field(default_factory=list)


class RadarScheduleResponse(BaseModel):
    """One schedule response."""

    model_config = ConfigDict(extra="forbid")

    schedule: RadarSchedule
    message: str = ""


class RadarScheduledRunResponse(BaseModel):
    """One scheduled run response."""

    model_config = ConfigDict(extra="forbid")

    scheduled_run: RadarScheduledRun
    notifications: list[LocalNotification] = Field(default_factory=list)
    message: str = ""


class RadarScheduledRunsResponse(BaseModel):
    """Scheduled run history response."""

    model_config = ConfigDict(extra="forbid")

    scheduled_runs: list[RadarScheduledRun] = Field(default_factory=list)


class RadarSchedulerStatusResponse(RadarSchedulerStatus):
    """Scheduler runtime status response."""


class RadarResultsResponse(BaseModel):
    """Radar results response."""

    model_config = ConfigDict(extra="forbid")

    results: list[RadarResult] = Field(default_factory=list)


class RadarResultResponse(BaseModel):
    """One updated radar result."""

    model_config = ConfigDict(extra="forbid")

    result: RadarResult
    message: str = ""


class RadarSaveInboxResponse(BaseModel):
    """Radar result saved to source inbox."""

    model_config = ConfigDict(extra="forbid")

    result: RadarResult
    inbox_item: OpportunityInboxItem
    message: str = ""


class RadarSaveTrackerResponse(BaseModel):
    """Radar result saved to tracker."""

    model_config = ConfigDict(extra="forbid")

    result: RadarResult
    tracker_id: str
    message: str = ""


class RadarAlertsResponse(BaseModel):
    """Radar alerts response."""

    model_config = ConfigDict(extra="forbid")

    alerts: list[RadarAlert] = Field(default_factory=list)


class RadarAlertResponse(BaseModel):
    """One radar alert response."""

    model_config = ConfigDict(extra="forbid")

    alert: RadarAlert
    message: str = ""


class RadarStatsResponse(RadarStats):
    """Radar dashboard stats."""
