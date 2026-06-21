"""Shared schema primitives for structured AI extraction."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    """Base schema that rejects unknown provider fields."""

    model_config = ConfigDict(extra="forbid")


class ConfidenceSummary(StrictSchema):
    """Overall confidence metadata for an extraction output."""

    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    low_confidence_fields: list[str] = Field(default_factory=list)
    needs_user_review: bool = True
    reason: str = ""


class EvidenceItem(StrictSchema):
    """Short evidence reference captured from source text."""

    text: str = ""
    source: Literal["resume", "job", "memory", "profile", "user_input", "unknown"] = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DomainSignal(StrictSchema):
    """Detected professional domain with supporting evidence."""

    domain: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class CredentialSignal(StrictSchema):
    """Professional license, certification, course or regulatory credential."""

    name: str = ""
    type: Literal[
        "professional_license",
        "certification",
        "course",
        "regulatory_training",
        "degree",
        "unknown",
    ] = "unknown"
    status: Literal["active", "expired", "completed", "ongoing", "unknown", "not_informed"] = (
        "unknown"
    )
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class LanguageSignal(StrictSchema):
    """Language evidence with an optional proficiency level."""

    language: str = ""
    level: Literal["basic", "intermediate", "advanced", "fluent", "native", "unknown"] = (
        "unknown"
    )
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
