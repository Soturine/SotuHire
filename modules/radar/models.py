"""Typed models for the local-first Job Radar."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return a timezone-aware timestamp."""
    return datetime.now(UTC)


RadarSourceType = Literal[
    "public_feed",
    "official_api",
    "manual_public_page",
    "manual_url",
    "recurring_csv_json",
]
RadarSourceStatus = Literal[
    "available",
    "experimental",
    "requires_official_api",
    "requires_user_key",
    "planned",
    "disabled",
    "error",
]
RadarResultStatus = Literal[
    "new",
    "matched",
    "ignored",
    "saved_to_inbox",
    "saved_to_tracker",
    "duplicate",
    "error",
    "archived",
]
RadarAlertStatus = Literal["unread", "read", "ignored", "saved"]


class JobRadarProfile(BaseModel):
    """Optional local candidate profile context used by radar runs."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = "Perfil local"
    resume_text: str = ""
    skills: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)


class JobWishlist(BaseModel):
    """What the user wants the radar to look for."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = "Wishlist principal"
    target_titles: list[str] = Field(default_factory=list)
    target_domains: list[str] = Field(default_factory=list)
    target_seniority: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_preferences: list[str] = Field(default_factory=list)
    work_model: str = ""
    employment_type: str = ""
    salary_min: int | None = Field(default=None, ge=0)
    salary_currency: str = "BRL"
    contract_types: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    companies_include: list[str] = Field(default_factory=list)
    companies_exclude: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)
    min_match_score: int = Field(default=70, ge=0, le=100)
    min_ats_score: int = Field(default=0, ge=0, le=100)
    notify_on_new_matches: bool = True
    notes: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    is_active: bool = True


class SavedSearch(BaseModel):
    """Reusable quick search criteria for radar runs."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = "Busca salva"
    query: str = ""
    keywords: list[str] = Field(default_factory=list)
    wishlist_id: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    is_active: bool = True


class RadarSource(BaseModel):
    """Configured source consulted by manual radar runs."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    source_type: RadarSourceType = "public_feed"
    url: str = ""
    docs_url: str = ""
    status: RadarSourceStatus = "available"
    is_active: bool = True
    requires_api_key: bool = False
    api_key_configured: bool = False
    max_results: int = Field(default=20, ge=1, le=100)
    timeout_seconds: float = Field(default=6.0, ge=1.0, le=30.0)
    rate_limit_seconds: float = Field(default=1.0, ge=0.2, le=60.0)
    last_checked_at: datetime | None = None
    last_error: str = ""
    notes: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PublicFeedSource(RadarSource):
    """Convenience model for public RSS/Atom feeds."""

    source_type: RadarSourceType = "public_feed"


class OfficialApiSource(RadarSource):
    """Official API source metadata without exposing secrets."""

    source_type: RadarSourceType = "official_api"
    status: RadarSourceStatus = "requires_official_api"


class ManualSource(RadarSource):
    """Manually configured public page or URL source."""

    source_type: RadarSourceType = "manual_public_page"


class SourceAdapter(BaseModel):
    """Document which adapter handles a radar source type."""

    model_config = ConfigDict(extra="forbid")

    source_type: RadarSourceType
    adapter_name: str
    supported: bool = True
    notes: str = ""


class RadarMatch(BaseModel):
    """Explainable score components for one radar result."""

    model_config = ConfigDict(extra="forbid")

    result_id: str = ""
    wishlist_id: str = ""
    radar_score: int = Field(default=0, ge=0, le=100)
    match_score: int = Field(default=0, ge=0, le=100)
    ats_score: int = Field(default=0, ge=0, le=100)
    wishlist_score: int = Field(default=0, ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    analysis_mode: Literal["local", "ai", "fallback"] = "local"
    provider_used: str = "local"
    warnings: list[str] = Field(default_factory=list)


class RadarResult(BaseModel):
    """One opportunity found by the radar and kept for manual review."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    source_id: str = ""
    source_name: str = ""
    source_type: RadarSourceType = "public_feed"
    wishlist_id: str = ""
    title: str
    company: str = ""
    url: str = ""
    location: str = ""
    work_model: str = ""
    employment_type: str = ""
    description: str = ""
    published_at: datetime | None = None
    captured_at: datetime = Field(default_factory=utc_now)
    normalized_text: str = ""
    dedupe_key: str = ""
    duplicate_of: str = ""
    match_score: int = Field(default=0, ge=0, le=100)
    ats_score: int = Field(default=0, ge=0, le=100)
    wishlist_score: int = Field(default=0, ge=0, le=100)
    radar_score: int = Field(default=0, ge=0, le=100)
    radar_status: RadarResultStatus = "new"
    already_in_inbox: bool = False
    already_in_tracker: bool = False
    warnings: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    analysis_mode: Literal["local", "ai", "fallback"] = "local"
    provider_used: str = "local"
    metadata: dict[str, object] = Field(default_factory=dict)


class RadarAlert(BaseModel):
    """Local alert generated from a relevant radar result."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    result_id: str = ""
    wishlist_id: str = ""
    title: str
    message: str
    score: int = Field(default=0, ge=0, le=100)
    status: RadarAlertStatus = "unread"
    created_at: datetime = Field(default_factory=utc_now)
    read_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class RadarRun(BaseModel):
    """History of one manual radar execution."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    source_ids: list[str] = Field(default_factory=list)
    wishlist_id: str = ""
    resume_used: bool = False
    total_sources: int = 0
    total_found: int = 0
    total_deduped: int = 0
    total_alerted: int = 0
    total_errors: int = 0
    duration_ms: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class RadarStats(BaseModel):
    """Compact dashboard statistics for the radar screen."""

    model_config = ConfigDict(extra="forbid")

    active_sources: int = 0
    total_sources: int = 0
    total_results: int = 0
    new_results: int = 0
    matched_results: int = 0
    unread_alerts: int = 0
    duplicates: int = 0
    source_errors: int = 0
    last_run_at: datetime | None = None
