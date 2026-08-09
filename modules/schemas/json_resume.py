"""Minimal JSON Resume compatible schemas with SotuHire evidence metadata."""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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


class SotuHireJSONResumeExtension(BaseModel):
    """Namespaced data that JSON Resume has no equivalent standard section for."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    professional_registrations: list[dict[str, Any]] = Field(
        default_factory=list,
        validation_alias=AliasChoices("professionalRegistrations", "professional_registrations"),
        serialization_alias="professionalRegistrations",
    )


class JSONResume(BaseModel):
    """Interoperable JSON Resume document plus SotuHire evidence metadata."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    schema_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("$schema", "schema_url"),
        serialization_alias="$schema",
    )
    basics: dict[str, Any] = Field(default_factory=dict)
    work: list[dict[str, Any]] = Field(default_factory=list)
    volunteer: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    awards: list[dict[str, Any]] = Field(default_factory=list)
    certificates: list[dict[str, Any]] = Field(default_factory=list)
    publications: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[dict[str, Any]] = Field(default_factory=list)
    languages: list[dict[str, Any]] = Field(default_factory=list)
    interests: list[dict[str, Any]] = Field(default_factory=list)
    references: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    sotuhire: SotuHireJSONResumeExtension = Field(
        default_factory=SotuHireJSONResumeExtension,
        validation_alias=AliasChoices("x-sotuhire", "sotuhire"),
        serialization_alias="x-sotuhire",
    )
    evidence: list[CareerEvidence] = Field(default_factory=list)
