"""DTOs for Universal Career Profile endpoints."""

from __future__ import annotations

from modules.profile.context import ProfileContext
from modules.profile.models import (
    ProfileConfidence,
    ProfileDeduplicationSuggestion,
    ProfileImportDraft,
    ProfileItem,
    UniversalCareerProfile,
)
from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdateRequest(BaseModel):
    """Update profile-level fields."""

    model_config = ConfigDict(extra="forbid")

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
    request_id: str = Field(default="", max_length=120)


class ProfileItemRequest(BaseModel):
    """Create one reviewed profile item."""

    model_config = ConfigDict(extra="forbid")

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
    confidence: ProfileConfidence = "high"
    sensitive: bool = False
    request_id: str = Field(default="", max_length=120)


class ProfileItemPatchRequest(BaseModel):
    """Patch one profile item."""

    model_config = ConfigDict(extra="forbid")

    type: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=5000)
    area: str | None = Field(default=None, max_length=160)
    domain: str | None = Field(default=None, max_length=160)
    institution: str | None = Field(default=None, max_length=240)
    organization: str | None = Field(default=None, max_length=240)
    status: str | None = Field(default=None, max_length=120)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    tags: list[str] | None = Field(default=None, max_length=80)
    skills: list[str] | None = Field(default=None, max_length=80)
    evidence: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, max_length=120)
    source_ref: str | None = Field(default=None, max_length=500)
    confidence: ProfileConfidence | None = None
    sensitive: bool | None = None
    request_id: str = Field(default="", max_length=120)


class ProfileImportTextRequest(BaseModel):
    """Import profile evidence from pasted text."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=200_000)
    source_type: str = Field(default="manual_notes", max_length=80)
    use_ai: bool = True
    language: str = Field(default="pt-BR", max_length=20)
    request_id: str = Field(default="", max_length=120)


class ProfileResponse(BaseModel):
    """Active profile response."""

    model_config = ConfigDict(extra="forbid")

    profile: UniversalCareerProfile
    message: str = ""


class ProfileItemResponse(BaseModel):
    """One profile item response."""

    model_config = ConfigDict(extra="forbid")

    item: ProfileItem
    message: str = ""


class ProfileImportTextResponse(ProfileImportDraft):
    """Draft extracted profile items."""


class ProfileDeduplicateResponse(BaseModel):
    """Profile dedupe suggestions."""

    model_config = ConfigDict(extra="forbid")

    suggestions: list[ProfileDeduplicationSuggestion] = Field(default_factory=list)
    message: str = ""


class ProfileContextResponse(BaseModel):
    """Profile context response."""

    model_config = ConfigDict(extra="forbid")

    context: ProfileContext
    message: str = ""
