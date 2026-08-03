"""Contracts for evidence-linked professional assets."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.evidence import EvidenceReviewStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class AssetType(StrEnum):
    RESUME_MASTER = "resume_master"
    RESUME_VARIANT = "resume_variant"
    COVER_LETTER = "cover_letter"
    RECRUITER_MESSAGE = "recruiter_message"
    PROFESSIONAL_BIO = "professional_bio"
    ABOUT_SECTION = "about_section"
    PORTFOLIO_SUMMARY = "portfolio_summary"
    PROJECT_HIGHLIGHT = "project_highlight"
    APPLICATION_KIT = "application_kit"


class AssetStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"
    STALE = "stale"


class ProfessionalAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(default_factory=lambda: uuid4().hex)
    asset_type: AssetType
    title: str = ""
    status: AssetStatus = AssetStatus.DRAFT
    content: str = ""
    structured_content: dict[str, Any] = Field(default_factory=dict)
    profile_id: str = ""
    target_opportunity_id: str = ""
    application_lab_session_id: str = ""
    evidence_scope_id: str = ""
    evidence_scope: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    document_snapshot_ids: list[str] = Field(default_factory=list)
    dependency_hash: str
    review_status: EvidenceReviewStatus = EvidenceReviewStatus.CANDIDATE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    stale_at: datetime | None = None
    stale_reason: str = ""

    @model_validator(mode="after")
    def enforce_review_boundary(self) -> ProfessionalAsset:
        self.source_refs = list(dict.fromkeys(filter(None, self.source_refs)))
        self.evidence_ids = list(dict.fromkeys(filter(None, self.evidence_ids)))
        self.document_snapshot_ids = list(
            dict.fromkeys(filter(None, self.document_snapshot_ids))
        )
        if self.status is AssetStatus.CONFIRMED:
            if self.content.strip() and not (self.source_refs or self.evidence_ids):
                raise ValueError("Asset com afirmações exige evidência antes da confirmação.")
            self.review_status = EvidenceReviewStatus.CONFIRMED
        if self.status is AssetStatus.STALE:
            self.review_status = EvidenceReviewStatus.STALE
            if self.stale_at is None:
                self.stale_at = utc_now()
        return self


__all__ = ["AssetStatus", "AssetType", "ProfessionalAsset", "utc_now"]
