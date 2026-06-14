"""Typed contracts for local career memory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

MemoryKind = Literal[
    "resume",
    "project",
    "experience",
    "education",
    "skill",
    "preference",
    "job_analysis",
    "opportunity",
    "feedback",
    "tracker_event",
    "github_profile",
    "github_repo",
    "portfolio",
    "commit_analysis",
    "readme_analysis",
    "project_evidence",
]


def utc_now() -> datetime:
    """Return a timezone-aware timestamp."""
    return datetime.now(UTC)


class CareerMemoryItem(BaseModel):
    """One locally persisted career fact or event."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    kind: MemoryKind
    title: str
    content: str
    source: str
    source_id: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CareerEvidence(BaseModel):
    """A traceable memory excerpt used by an analysis."""

    model_config = ConfigDict(extra="forbid")

    memory_id: str
    title: str
    source: str
    kind: MemoryKind | None = None
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    selection_reason: str = ""
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class CareerMemoryQuery(BaseModel):
    """Local retrieval query with optional exact filters."""

    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    filters: dict[str, str] = Field(default_factory=dict)


class CareerFeedback(BaseModel):
    """Manual outcome feedback converted into career memory."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: str | None = None
    rating: Literal["yes", "partial", "no"]
    reason: str = ""
    change_requested: str = ""
    applied: bool | None = None
    response_received: bool | None = None


class EvidenceFeedback(BaseModel):
    """Useful/not-useful feedback for one retrieved memory evidence."""

    model_config = ConfigDict(extra="forbid")

    memory_id: str
    useful: bool
    query: str = ""
    analysis_id: str | None = None


class MemoryPrivacySettings(BaseModel):
    """Explicit flags controlling local and external memory use."""

    model_config = ConfigDict(extra="forbid")

    use_memory: bool = True
    send_relevant_context_to_gemini: bool = False


class MemoryExport(BaseModel):
    """Portable local memory bundle."""

    model_config = ConfigDict(extra="forbid")

    format_version: str = "1"
    exported_at: datetime = Field(default_factory=utc_now)
    items: list[CareerMemoryItem] = Field(default_factory=list)
