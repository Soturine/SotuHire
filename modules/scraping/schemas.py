"""Typed contracts for responsible public scraping."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class ScrapedOpportunity(BaseModel):
    """A public opportunity collected and normalized from one source."""

    model_config = ConfigDict(extra="forbid")

    source: str
    source_url: str
    title: str
    company: str | None = None
    location: str | None = None
    modality: str | None = None
    seniority: str | None = None
    contract_type: str | None = None
    salary_text: str | None = None
    description: str
    requirements: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content_hash: str
    confidence: float = Field(default=0.5, ge=0, le=1)


class ScrapingSource(BaseModel):
    """Configurable public collection source."""

    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    url: str
    enabled: bool = False
    max_items: int = Field(default=20, ge=1, le=200)
    delay_seconds: float = Field(default=2.0, ge=0.2, le=60)
    selectors: dict[str, str] = Field(default_factory=dict)
    notes: str = ""


class SourceSafety(BaseModel):
    """Preview of access constraints before collection."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    domain: str
    detected_type: str
    robots_status: str
    authentication_required: bool = False
    warning: str = ""


class FetchResult(BaseModel):
    """One HTTP fetch result with safe metadata."""

    model_config = ConfigDict(extra="forbid")

    url: str
    status_code: int
    content_type: str = ""
    text: str = ""
    from_cache: bool = False
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CollectionResult(BaseModel):
    """Summary returned by every connector."""

    model_config = ConfigDict(extra="forbid")

    source: ScrapingSource
    opportunities: list[ScrapedOpportunity] = Field(default_factory=list)
    new_count: int = 0
    duplicate_count: int = 0
    updated_count: int = 0
    failures: list[str] = Field(default_factory=list)
    scraping_performed: bool = False
