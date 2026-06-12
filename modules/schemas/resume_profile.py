"""Structured profile extracted from a resume supplied by the user."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ResumeProfileSchema(BaseModel):
    """Normalized resume facts used for review and analysis."""

    model_config = ConfigDict(extra="forbid")

    name: str = ""
    summary: str = ""
    education: list[str] = Field(default_factory=list)
    experiences: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    raw_text: str = ""
    source_type: str = "text"
