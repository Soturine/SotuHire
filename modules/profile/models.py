"""Universal career profile models for local-first SotuHire workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

ProfileConfidence = Literal["low", "medium", "high"]


def utc_now() -> datetime:
    """Return a timezone-aware timestamp."""
    return datetime.now(UTC)


class ProfileItem(BaseModel):
    """One evidence-backed universal career profile item."""

    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(default_factory=lambda: uuid4().hex)
    type: str = Field(default="other", max_length=80)
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=5000)
    area: str | None = Field(default=None, max_length=160)
    domain: str | None = Field(default=None, max_length=160)
    institution: str | None = Field(default=None, max_length=240)
    organization: str | None = Field(default=None, max_length=240)
    status: str | None = Field(default=None, max_length=120)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=80)
    skills: list[str] = Field(default_factory=list, max_length=80)
    evidence: str | None = Field(default=None, max_length=5000)
    source: str = Field(default="manual", max_length=120)
    source_ref: str | None = Field(default=None, max_length=500)
    confidence: ProfileConfidence = "medium"
    confirmed_by_user: bool = False
    sensitive: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ProfileSourceSummary(BaseModel):
    """Compact summary for one profile source."""

    model_config = ConfigDict(extra="forbid")

    source: str
    source_type: str = ""
    item_count: int = 0
    last_imported_at: datetime | None = None


class UniversalCareerProfile(BaseModel):
    """Universal, local-first career profile persisted on disk."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = "default"
    display_name: str | None = Field(default=None, max_length=160)
    headline: str | None = Field(default=None, max_length=240)
    summary: str | None = Field(default=None, max_length=5000)
    primary_domains: list[str] = Field(default_factory=list, max_length=40)
    secondary_domains: list[str] = Field(default_factory=list, max_length=40)
    career_moments: list[str] = Field(default_factory=list, max_length=40)
    target_roles: list[str] = Field(default_factory=list, max_length=60)
    target_seniority: list[str] = Field(default_factory=list, max_length=30)
    preferred_locations: list[str] = Field(default_factory=list, max_length=60)
    preferred_work_models: list[str] = Field(default_factory=list, max_length=20)
    preferred_contract_types: list[str] = Field(default_factory=list, max_length=30)
    constraints: list[ProfileItem] = Field(default_factory=list, max_length=80)
    items: list[ProfileItem] = Field(default_factory=list)
    source_summaries: list[ProfileSourceSummary] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)


class UniversalCareerProfileState(BaseModel):
    """Local profile state prepared for future multiple profiles."""

    model_config = ConfigDict(extra="forbid")

    active_profile_id: str = "default"
    profiles: list[UniversalCareerProfile] = Field(default_factory=list)


class ProfileDeduplicationSuggestion(BaseModel):
    """A safe duplicate suggestion that preserves all profile evidence."""

    model_config = ConfigDict(extra="forbid")

    suggestion_id: str = Field(default_factory=lambda: uuid4().hex)
    item_ids: list[str] = Field(default_factory=list, min_length=2, max_length=10)
    reason: str = ""
    confidence: ProfileConfidence = "medium"
    proposed_title: str = ""
    proposed_description: str | None = None
    sources: list[str] = Field(default_factory=list)


class ProfileImportDraft(BaseModel):
    """Draft result from profile text import."""

    model_config = ConfigDict(extra="forbid")

    items: list[ProfileItem] = Field(default_factory=list)
    detected_domains: list[str] = Field(default_factory=list)
    career_moments: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    questions_to_confirm: list[str] = Field(default_factory=list)
    provider_used: str = "local"
    requested_provider: str = "local"
    analysis_mode: str = "local"
    needs_user_review: bool = True
