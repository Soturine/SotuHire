"""Typed contracts shared by the local companion API and browser extension."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

CollectionMethod = Literal[
    "public_scraping",
    "manual_url",
    "rss",
    "company_career_page",
    "browser_assisted_capture",
    "demo_fixture",
]


def utc_now() -> datetime:
    return datetime.now(UTC)


class BrowserCapturePayload(BaseModel):
    """Visible page content explicitly captured by the browser companion."""

    model_config = ConfigDict(extra="forbid")

    page_title: str = Field(default="", max_length=500)
    url: str = Field(max_length=2048)
    domain: str = Field(default="", max_length=255)
    visible_text: str = Field(default="", max_length=200_000)
    job_title: str = Field(default="", max_length=500)
    company: str = Field(default="", max_length=500)
    location: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=100_000)
    captured_at: datetime = Field(default_factory=utc_now)
    collection_method: CollectionMethod = "browser_assisted_capture"

    @field_validator("url")
    @classmethod
    def validate_page_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("A captura deve usar uma URL HTTP ou HTTPS.")
        return value

    @field_validator(
        "page_title",
        "domain",
        "visible_text",
        "job_title",
        "company",
        "location",
        "description",
        mode="before",
    )
    @classmethod
    def normalize_string_fields(cls, value: object) -> str:
        return str(value or "")


class CompanionCaptureRecord(BaseModel):
    """Persisted local capture and its optional action results."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    capture: BrowserCapturePayload
    status: Literal["captured", "analyzed", "tracked"] = "captured"
    analysis_summary: dict[str, object] = Field(default_factory=dict)
    tracker_id: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CaptureActionRequest(BaseModel):
    """Request accepted by analyze and tracker endpoints."""

    model_config = ConfigDict(extra="forbid")

    capture: BrowserCapturePayload | None = None
    capture_id: str = Field(default="", max_length=64)
    use_ai: bool = False


class ApplicationBatchPayload(BaseModel):
    """Previously applied jobs visible on a manually opened tracker page."""

    model_config = ConfigDict(extra="forbid")

    applications: list[BrowserCapturePayload] = Field(min_length=1, max_length=500)


class CompanionAnalysisContext(BaseModel):
    """Local-only active context written by the Streamlit app."""

    model_config = ConfigDict(extra="forbid")

    resume_text: str = Field(default="", max_length=300_000)
    preferences: dict[str, object] = Field(default_factory=dict)
    provider: str = Field(default="local", max_length=50)
    updated_at: datetime = Field(default_factory=utc_now)


class CompanionResponse(BaseModel):
    """Short response safe to display in the extension popup."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    message: str
    capture_id: str = ""
    match_score: int | None = None
    ats_score: int | None = None
    recommendation: str = ""
    provider: str = ""
    tracker_id: str = ""
    app_url: str = "http://127.0.0.1:8501"
