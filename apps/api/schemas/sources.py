"""DTOs for source collection endpoints."""

from __future__ import annotations

from modules.scraping.browser_session import DEFAULT_CDP_URL
from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedBrowserStatusResponse(BaseModel):
    """Status of the local Chromium CDP session."""

    model_config = ConfigDict(extra="forbid")

    available: bool
    endpoint: str = DEFAULT_CDP_URL
    browser: str = ""
    message: str = ""


class AuthenticatedBrowserLaunchRequest(BaseModel):
    """Request to open the dedicated browser for manual login."""

    model_config = ConfigDict(extra="forbid")

    start_url: str = Field(default="https://www.linkedin.com/jobs/", max_length=2048)
    browser_cdp_url: str = Field(default=DEFAULT_CDP_URL, max_length=200)
    request_id: str = Field(default="", max_length=120)


class AuthenticatedBrowserCollectRequest(BaseModel):
    """Request to collect from an already-authenticated authorized browser."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="LinkedIn autorizado", min_length=1, max_length=200)
    url: str = Field(default="https://www.linkedin.com/jobs/", max_length=2048)
    browser_cdp_url: str = Field(default=DEFAULT_CDP_URL, max_length=200)
    max_items: int = Field(default=20, ge=1, le=100)
    max_pages: int = Field(default=3, ge=1, le=20)
    delay_seconds: float = Field(default=2.0, ge=0.2, le=60)
    authorized_use: bool = False
    authorization_reference: str = Field(default="", max_length=500)
    request_id: str = Field(default="", max_length=120)


class AuthenticatedBrowserOpportunityItem(BaseModel):
    """Small public summary of a collected opportunity."""

    model_config = ConfigDict(extra="forbid")

    title: str
    company: str = ""
    source_url: str = ""
    confidence: float = Field(ge=0, le=1)


class AuthenticatedBrowserCollectResponse(BaseModel):
    """Result of an authenticated browser collection run."""

    model_config = ConfigDict(extra="forbid")

    new_count: int = 0
    duplicate_count: int = 0
    updated_count: int = 0
    failures: list[str] = Field(default_factory=list)
    opportunities: list[AuthenticatedBrowserOpportunityItem] = Field(default_factory=list)
