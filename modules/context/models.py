"""Typed models for the Career Context Engine."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CareerContextPurpose(StrEnum):
    """Known context purposes across SotuHire product flows."""

    GENERIC = "generic"
    WISHLIST = "wishlist"
    RADAR = "radar"
    MATCH = "match"
    ATS = "ats"
    TAILOR = "tailor"
    TRACKER = "tracker"
    NOTIFICATIONS = "notifications"
    SOURCES = "sources"
    GITHUB = "github"
    DASHBOARD = "dashboard"


class CareerContextEvidence(BaseModel):
    """One traceable evidence item available to a product flow."""

    model_config = ConfigDict(extra="forbid")

    title: str
    content: str = ""
    kind: str = "profile"
    source: str = ""
    confidence: Literal["low", "medium", "high"] = "medium"
    confirmed_by_user: bool = False
    sensitive: bool = False
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CareerContext(BaseModel):
    """Unified local career context assembled from profile, memory and product signals."""

    model_config = ConfigDict(extra="forbid")

    purpose: CareerContextPurpose
    profile_summary: str = ""
    goals: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    work_models: list[str] = Field(default_factory=list)
    contract_types: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    evidence: list[CareerContextEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    privacy_notes: list[str] = Field(default_factory=list)
