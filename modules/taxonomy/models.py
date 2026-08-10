"""Versioned, reviewable occupation and skill taxonomy contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


TaxonomySystem = Literal["cbo", "qbq", "esco", "onet"]


class MappingMethod(StrEnum):
    EXACT = "exact"
    ALIAS = "alias"
    NORMALIZED = "normalized"
    TAXONOMY_CROSSWALK = "taxonomy_crosswalk"
    SEMANTIC_CANDIDATE = "semantic_candidate"
    MANUAL = "manual"


class TaxonomyDatasetManifest(BaseModel):
    """Reproducible metadata for an official, locally cached dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    system: TaxonomySystem
    version: str = Field(min_length=1, max_length=80)
    source_url: str
    license_name: str
    license_url: str = ""
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    retrieved_at: datetime = Field(default_factory=utc_now)


class NormalizedOccupation(BaseModel):
    """Canonical occupation label; CBO never implies professional regulation."""

    model_config = ConfigDict(extra="forbid")

    occupation_id: str = Field(default_factory=lambda: uuid4().hex)
    canonical_title: str
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    taxonomy_refs: list[str] = Field(default_factory=list)
    family: str = ""
    qualification_level: str = ""
    knowledge: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    attitudes: list[str] = Field(default_factory=list)


class NormalizedSkill(BaseModel):
    """Canonical skill label assembled without confirming candidate possession."""

    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(default_factory=lambda: uuid4().hex)
    canonical_label: str
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    taxonomy_refs: list[str] = Field(default_factory=list)


class TaxonomyMapping(BaseModel):
    """One transparent mapping candidate or human-reviewed decision."""

    model_config = ConfigDict(extra="forbid")

    mapping_id: str = Field(default_factory=lambda: uuid4().hex)
    source_text: str
    target_id: str
    target_label: str
    taxonomy_ref: str
    match_method: MappingMethod
    confidence: float = Field(ge=0, le=1)
    review_status: Literal["candidate", "confirmed", "rejected"] = "candidate"
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def semantic_matches_require_review(self) -> TaxonomyMapping:
        if self.match_method == MappingMethod.SEMANTIC_CANDIDATE:
            self.review_status = "candidate"
            self.reviewed_at = None
        return self


__all__ = [
    "MappingMethod",
    "NormalizedOccupation",
    "NormalizedSkill",
    "TaxonomyDatasetManifest",
    "TaxonomyMapping",
    "TaxonomySystem",
]
