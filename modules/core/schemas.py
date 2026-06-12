"""Core data schemas for SotuHire.

These models are intentionally small and dependency-light so the MVP can evolve
without coupling business rules to Streamlit or any specific AI provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


class Seniority(StrEnum):
    INTERNSHIP = "internship"
    TRAINEE = "trainee"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    UNKNOWN = "unknown"


class SourceStatus(StrEnum):
    MANUAL_ONLY = "manual_only"
    PLANNED = "planned"
    EXPERIMENTAL = "experimental"
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    DEPRECATED = "deprecated"


@dataclass(slots=True)
class JobSearchQuery:
    role: str
    seniority: Seniority = Seniority.UNKNOWN
    modality: str | None = None
    location: str | None = None
    skills: list[str] = field(default_factory=list)
    language: str = "pt-BR"


@dataclass(slots=True)
class JobPosting:
    title: str
    company: str | None = None
    url: str | None = None
    source: str | None = None
    description: str | None = None
    location: str | None = None
    modality: str | None = None
    seniority: Seniority = Seniority.UNKNOWN
    posted_at: date | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScoreBreakdown:
    match_score: int | None = None
    ats_score: int | None = None
    risk_score: int | None = None
    linkedin_score: int | None = None
    portfolio_score: int | None = None
    lattes_score: int | None = None
    readiness_score: int | None = None


@dataclass(slots=True)
class AnalysisReport:
    recommendation: str
    scores: ScoreBreakdown
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
