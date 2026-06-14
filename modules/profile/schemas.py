"""Typed persistent career profile contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CareerProfile(BaseModel):
    """Consolidated professional profile built from local evidence."""

    model_config = ConfigDict(extra="forbid")

    target_roles: list[str] = Field(default_factory=list)
    likely_seniority: str | None = None
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    education_summary: list[str] = Field(default_factory=list)
    experience_summary: list[str] = Field(default_factory=list)
    project_highlights: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    preferred_modalities: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_contracts: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    recurring_gaps: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)


class InferredPreferences(BaseModel):
    """Editable preferences inferred from local history."""

    model_config = ConfigDict(extra="forbid")

    target_roles: list[str] = Field(default_factory=list)
    modalities: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    contracts: list[str] = Field(default_factory=list)
    seniorities: list[str] = Field(default_factory=list)
    relevant_skills: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
