"""Generalist local profile context used by future AI-assisted workflows."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.evidence import EvidenceReviewStatus


class ProfileContextItem(BaseModel):
    """One evidence-backed profile signal.

    The context is intentionally generic: it must support technical, academic,
    healthcare, legal, artistic, industrial and other career paths.
    """

    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    description: str | None = None
    area: str | None = None
    domain: str | None = None
    source: str | None = None
    source_ref: str | None = None
    review_status: EvidenceReviewStatus = EvidenceReviewStatus.CANDIDATE
    evidence: str | None = None
    confidence: Literal["low", "medium", "high"] = "medium"
    confirmed_by_user: bool = False
    sensitive: bool = False

    @model_validator(mode="after")
    def normalize_review_status(self) -> ProfileContextItem:
        if self.confirmed_by_user:
            self.review_status = EvidenceReviewStatus.CONFIRMED
        elif self.review_status == EvidenceReviewStatus.CONFIRMED:
            self.confirmed_by_user = True
        elif self.review_status == EvidenceReviewStatus.CANDIDATE and self.source_ref:
            self.review_status = EvidenceReviewStatus.SOURCED
        if self.review_status in {EvidenceReviewStatus.REJECTED, EvidenceReviewStatus.STALE}:
            self.confirmed_by_user = False
        return self


class ProfileBucketReconciliation(BaseModel):
    """Source decision for one Universal/legacy profile bucket."""

    model_config = ConfigDict(extra="forbid")

    bucket: str
    source: Literal["universal", "legacy_fallback", "merged_for_review", "empty"]
    universal_count: int = 0
    legacy_count: int = 0
    conflict: bool = False
    note: str = ""


class ProfileReconciliationReport(BaseModel):
    """Reviewable bucket-level reconciliation without deleting either store."""

    model_config = ConfigDict(extra="forbid")

    buckets: list[ProfileBucketReconciliation] = Field(default_factory=list)
    requires_review: bool = False


class ProfileContext(BaseModel):
    """Safe, compact context assembled from local profile evidence."""

    model_config = ConfigDict(extra="forbid")

    identity: dict[str, object] = Field(default_factory=dict)
    career_goals: list[str] = Field(default_factory=list)
    education: list[ProfileContextItem] = Field(default_factory=list)
    experiences: list[ProfileContextItem] = Field(default_factory=list)
    academic_experiences: list[ProfileContextItem] = Field(default_factory=list)
    projects: list[ProfileContextItem] = Field(default_factory=list)
    certifications_and_registries: list[ProfileContextItem] = Field(default_factory=list)
    skills: list[ProfileContextItem] = Field(default_factory=list)
    languages: list[ProfileContextItem] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    constraint_items: list[ProfileContextItem] = Field(default_factory=list)
    application_history_signals: list[str] = Field(default_factory=list)
    reconciliation: ProfileReconciliationReport = Field(default_factory=ProfileReconciliationReport)
