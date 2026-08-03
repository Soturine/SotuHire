"""Minimal JSON Resume compatible schemas with SotuHire evidence metadata."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CareerEvidence(BaseModel):
    """Evidence that supports a career fact used by the resume tailor."""

    model_config = ConfigDict(extra="forbid")

    fact: str = Field(min_length=1)
    source: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    can_use_in_resume: bool = True
    last_verified_at: str | None = None
    source_ref: str | None = None
    profile_item_id: str | None = None


class JSONResume(BaseModel):
    """Interoperable JSON Resume document plus SotuHire evidence metadata."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_url: str | None = Field(default=None, alias="$schema")
    basics: dict = Field(default_factory=dict)
    work: list[dict] = Field(default_factory=list)
    volunteer: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    awards: list[dict] = Field(default_factory=list)
    certificates: list[dict] = Field(default_factory=list)
    publications: list[dict] = Field(default_factory=list)
    skills: list[dict] = Field(default_factory=list)
    languages: list[dict] = Field(default_factory=list)
    interests: list[dict] = Field(default_factory=list)
    references: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)
    evidence: list[CareerEvidence] = Field(default_factory=list)
