"""Typed models for the Career Context Engine."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.evidence import EvidenceReviewStatus, EvidenceSourceLocation


class CareerContextPurpose(StrEnum):
    """Known context purposes across SotuHire product flows."""

    GENERIC = "generic"
    WISHLIST = "wishlist"
    RADAR = "radar"
    MATCH = "match"
    ATS = "ats"
    TAILOR = "tailor"
    TRACKER = "tracker"
    NOTIFICATIONS = "notifications"
    SOURCES = "sources"
    EXTENSION = "extension"
    GITHUB = "github"
    DASHBOARD = "dashboard"
    ACADEMIC = "academic"
    LATTES = "lattes"
    PUBLIC_EXAMS = "public_exams"


class CareerContextEvidence(BaseModel):
    """One traceable evidence item available to a product flow."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = ""
    title: str
    content: str = ""
    kind: str = "profile"
    source: str = ""
    source_ref: str = ""
    source_location: EvidenceSourceLocation = Field(default_factory=EvidenceSourceLocation)
    content_hash: str = ""
    observed_at: datetime | None = None
    review_status: EvidenceReviewStatus = EvidenceReviewStatus.CANDIDATE
    confidence: Literal["low", "medium", "high"] = "medium"
    confirmed_by_user: bool = False
    sensitive: bool = False
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def normalize_review_and_identity(self) -> CareerContextEvidence:
        digest = _evidence_digest(self)
        if not self.content_hash:
            self.content_hash = digest
        if not self.evidence_id:
            self.evidence_id = f"evidence-{digest[:24]}"
        if self.confirmed_by_user:
            self.review_status = EvidenceReviewStatus.CONFIRMED
        elif self.review_status == EvidenceReviewStatus.CONFIRMED:
            self.confirmed_by_user = True
        elif self.review_status == EvidenceReviewStatus.CANDIDATE and self.source_ref:
            self.review_status = EvidenceReviewStatus.SOURCED
        if self.review_status in {EvidenceReviewStatus.REJECTED, EvidenceReviewStatus.STALE}:
            self.confirmed_by_user = False
        return self


class EvidenceScope(BaseModel):
    """Immutable selection boundary shared by analysis and external-AI flows."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scope_id: str = Field(default_factory=lambda: f"scope-{uuid4().hex}")
    purpose: CareerContextPurpose
    selected_evidence_ids: tuple[str, ...] = ()
    selected_source_refs: tuple[str, ...] = ()
    external_ai_opt_in: bool = False
    sensitive_evidence_opt_in: bool = False
    dependency_hash: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_evidence(
        cls,
        *,
        purpose: CareerContextPurpose,
        evidence: list[CareerContextEvidence],
        selected_evidence_ids: list[str] | tuple[str, ...] | None = None,
        selected_source_refs: list[str] | tuple[str, ...] | None = None,
        external_ai_opt_in: bool = False,
        sensitive_evidence_opt_in: bool = False,
    ) -> EvidenceScope:
        ids = tuple(
            dict.fromkeys(
                selected_evidence_ids
                if selected_evidence_ids is not None
                else [
                    item.evidence_id
                    for item in evidence
                    if item.review_status
                    not in {EvidenceReviewStatus.REJECTED, EvidenceReviewStatus.STALE}
                ]
            )
        )
        refs = tuple(dict.fromkeys(selected_source_refs or ()))
        selected = [item for item in evidence if item.evidence_id in ids or item.source_ref in refs]
        dependency_hash = hashlib.sha256(
            json.dumps(
                [
                    [item.evidence_id, item.content_hash, item.review_status.value, item.sensitive]
                    for item in sorted(selected, key=lambda value: value.evidence_id)
                ],
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return cls(
            purpose=purpose,
            selected_evidence_ids=ids,
            selected_source_refs=refs,
            external_ai_opt_in=external_ai_opt_in,
            sensitive_evidence_opt_in=sensitive_evidence_opt_in,
            dependency_hash=dependency_hash,
        )

    def select(
        self,
        evidence: list[CareerContextEvidence],
        *,
        for_external_ai: bool = False,
    ) -> list[CareerContextEvidence]:
        selected = [
            item
            for item in evidence
            if item.evidence_id in self.selected_evidence_ids
            or (item.source_ref and item.source_ref in self.selected_source_refs)
        ]
        selected = [
            item
            for item in selected
            if item.review_status not in {EvidenceReviewStatus.REJECTED, EvidenceReviewStatus.STALE}
        ]
        if not for_external_ai:
            return selected
        if not self.external_ai_opt_in:
            return []
        return [
            item
            for item in selected
            if item.review_status == EvidenceReviewStatus.CONFIRMED
            and (not item.sensitive or self.sensitive_evidence_opt_in)
        ]


class CareerContext(BaseModel):
    """Unified local career context assembled from profile, memory and product signals."""

    model_config = ConfigDict(extra="forbid")

    purpose: CareerContextPurpose
    profile_summary: str = ""
    goals: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    work_models: list[str] = Field(default_factory=list)
    contract_types: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    evidence: list[CareerContextEvidence] = Field(default_factory=list)
    evidence_scope: EvidenceScope | None = None
    warnings: list[str] = Field(default_factory=list)
    privacy_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def create_default_scope(self) -> CareerContext:
        if self.evidence_scope is None:
            self.evidence_scope = EvidenceScope.from_evidence(
                purpose=self.purpose,
                evidence=self.evidence,
            )
        return self


def _evidence_digest(item: CareerContextEvidence) -> str:
    payload = {
        "title": item.title,
        "content": item.content,
        "kind": item.kind,
        "source": item.source,
        "source_ref": item.source_ref,
        "source_location": item.source_location.model_dump(mode="json"),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
