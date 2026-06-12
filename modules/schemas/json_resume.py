"""Minimal JSON Resume compatible schemas with SotuHire evidence metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CareerEvidence(BaseModel):
    """Evidence that supports a career fact used by the resume tailor."""

    fact: str
    source: str
    evidence: str
    confidence: float = Field(ge=0, le=1)
    can_use_in_resume: bool = True
    last_verified_at: str | None = None


class JSONResume(BaseModel):
    """Lightweight JSON Resume-inspired model.

    This is intentionally partial. The full standard can be imported/exported later.
    """

    basics: dict = Field(default_factory=dict)
    work: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    skills: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    certificates: list[dict] = Field(default_factory=list)
    languages: list[dict] = Field(default_factory=list)
    evidence: list[CareerEvidence] = Field(default_factory=list)
