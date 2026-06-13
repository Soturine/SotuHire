"""Typed contracts for safe, manual-first search intelligence."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SearchStrategyInput(BaseModel):
    """Career intent used to build a search strategy without network access."""

    model_config = ConfigDict(extra="forbid")

    target_role: str
    skills: list[str] = Field(default_factory=list)
    location: str = ""
    modality: str = ""
    seniority: str = ""
    target_companies: list[str] = Field(default_factory=list)
    contract: str = ""


class SourceSuggestion(BaseModel):
    """A manual search source with an explicit safe access mode."""

    model_config = ConfigDict(extra="forbid")

    name: str
    url: str
    reason: str
    access_mode: str = "manual"


class HiddenJobsRadarPlan(BaseModel):
    """Strategic hidden-jobs guidance that performs no scraping."""

    model_config = ConfigDict(extra="forbid")

    alternative_roles: list[str] = Field(default_factory=list)
    target_company_ideas: list[str] = Field(default_factory=list)
    manual_alerts: list[str] = Field(default_factory=list)
    generic_job_risks: list[str] = Field(default_factory=list)
    scraping_performed: bool = False


class SearchIntelligencePlan(BaseModel):
    """Complete safe search plan shown in advanced mode."""

    model_config = ConfigDict(extra="forbid")

    queries: list[str] = Field(default_factory=list)
    sources: list[SourceSuggestion] = Field(default_factory=list)
    weekly_plan: list[str] = Field(default_factory=list)
    radar: HiddenJobsRadarPlan
    scraping_performed: bool = False
