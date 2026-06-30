"""Generalist local profile context used by future AI-assisted workflows."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProfileContextItem(BaseModel):
    """One evidence-backed profile signal.

    The context is intentionally generic: it must support technical, academic,
    healthcare, legal, artistic, industrial and other career paths.
    """

    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    description: str | None = None
    area: str | None = None
    domain: str | None = None
    source: str | None = None
    evidence: str | None = None
    confidence: Literal["low", "medium", "high"] = "medium"
    confirmed_by_user: bool = False
    sensitive: bool = False


class ProfileContext(BaseModel):
    """Safe, compact context assembled from local profile evidence."""

    model_config = ConfigDict(extra="forbid")

    identity: dict[str, object] = Field(default_factory=dict)
    career_goals: list[str] = Field(default_factory=list)
    education: list[ProfileContextItem] = Field(default_factory=list)
    experiences: list[ProfileContextItem] = Field(default_factory=list)
    academic_experiences: list[ProfileContextItem] = Field(default_factory=list)
    projects: list[ProfileContextItem] = Field(default_factory=list)
    certifications_and_registries: list[ProfileContextItem] = Field(default_factory=list)
    skills: list[ProfileContextItem] = Field(default_factory=list)
    languages: list[ProfileContextItem] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    application_history_signals: list[str] = Field(default_factory=list)
