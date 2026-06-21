"""Structured schema for professional domain classification."""

from __future__ import annotations

from pydantic import Field

from modules.ai.schemas.common import DomainSignal, StrictSchema


class RegulatedProfessionSignal(StrictSchema):
    """Credential signal that may indicate a regulated profession."""

    credential: str
    domain: str = "unknown"
    category: str = "professional_license"
    evidence: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AliasDetection(StrictSchema):
    """Normalized alias detected in the source text."""

    original: str
    normalized_name: str
    category: str = "other"
    domain: str = "unknown"
    evidence: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DomainClassificationOutput(StrictSchema):
    """Domain classification output for resumes, jobs, projects and posts."""

    primary_domain: DomainSignal = Field(default_factory=DomainSignal)
    secondary_domains: list[DomainSignal] = Field(default_factory=list)
    requirement_categories_detected: list[str] = Field(default_factory=list)
    regulated_profession_signals: list[RegulatedProfessionSignal] = Field(default_factory=list)
    aliases_detected: list[AliasDetection] = Field(default_factory=list)
    domain_notes: list[str] = Field(default_factory=list)
    needs_review: bool = True
