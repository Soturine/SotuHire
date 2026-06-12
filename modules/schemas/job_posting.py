"""Structured job posting extracted from pasted descriptions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

JobModality = Literal["remote", "hybrid", "onsite", "unknown"]


class JobPostingSchema(BaseModel):
    """Normalized vacancy facts detected from user-provided text."""

    model_config = ConfigDict(extra="forbid")

    title: str = ""
    company: str = ""
    location: str = ""
    modality: JobModality = "unknown"
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    contract: str = ""
    seniority: str = ""
    required_skills: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    english_required: bool = False
    ats_keywords: list[str] = Field(default_factory=list)
    raw_text: str = ""
