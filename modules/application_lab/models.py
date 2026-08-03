"""Strict domain contracts for Application Lab and Resume Studio."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.evidence import EvidenceReviewStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class LabModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ApplicationLabStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    ANALYZING = "analyzing"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class SuggestionStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class ResumeEntry(LabModel):
    entry_id: str = Field(default_factory=lambda: uuid4().hex)
    entry_type: str = "item"
    title: str = ""
    subtitle: str = ""
    content: str = ""
    start_date: str = ""
    end_date: str = ""
    position: int = Field(default=0, ge=0)
    enabled: bool = True
    source_profile_item_ids: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    review_status: EvidenceReviewStatus = EvidenceReviewStatus.CANDIDATE
    confirmed_by_user: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def normalize_review_status(self) -> ResumeEntry:
        if self.confirmed_by_user:
            self.review_status = EvidenceReviewStatus.CONFIRMED
        elif self.review_status == EvidenceReviewStatus.CONFIRMED:
            self.confirmed_by_user = True
        elif self.review_status == EvidenceReviewStatus.CANDIDATE and self.source_refs:
            self.review_status = EvidenceReviewStatus.SOURCED
        if self.review_status in {EvidenceReviewStatus.REJECTED, EvidenceReviewStatus.STALE}:
            self.confirmed_by_user = False
        return self


class ResumeSection(LabModel):
    section_id: str = Field(default_factory=lambda: uuid4().hex)
    section_type: str
    title: str
    position: int = Field(default=0, ge=0)
    enabled: bool = True
    content: str = ""
    entries: list[ResumeEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MasterResume(LabModel):
    master_resume_id: str = Field(default_factory=lambda: uuid4().hex)
    profile_id: str = ""
    title: str = "Currículo Mestre"
    target_role: str = ""
    summary: str = ""
    raw_text: str = ""
    source_type: Literal["manual", "profile", "pdf", "docx", "txt", "json_resume"] = "manual"
    source_refs: list[str] = Field(default_factory=list)
    source_profile_item_ids: list[str] = Field(default_factory=list)
    sections: list[ResumeSection] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ResumeVariantChange(LabModel):
    change_id: str = Field(default_factory=lambda: uuid4().hex)
    change_type: Literal["added", "removed", "edited", "reordered"]
    section: str = ""
    before: str = ""
    after: str = ""
    reason: str = ""
    evidence_used: list[str | dict[str, Any]] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    warning: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ResumeVariant(LabModel):
    resume_variant_id: str = Field(default_factory=lambda: uuid4().hex)
    master_resume_id: str
    job_snapshot_id: str = ""
    title: str = "Variante"
    target_role: str = ""
    sections: list[ResumeSection] = Field(default_factory=list)
    source_profile_item_ids: list[str] = Field(default_factory=list)
    change_set: list[ResumeVariantChange] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ResumeTemplate(LabModel):
    template_id: str
    name: str
    description: str = ""
    ats_safe: bool = True
    page_sizes: list[Literal["A4", "Letter"]] = Field(default_factory=lambda: ["A4", "Letter"])
    configuration: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ResumeExport(LabModel):
    export_id: str = Field(default_factory=lambda: uuid4().hex)
    master_resume_id: str = ""
    resume_variant_id: str = ""
    template_id: str = "classic"
    format: Literal["json_resume", "pdf", "docx"] = "json_resume"
    status: Literal["ready", "pending", "failed"] = "ready"
    file_name: str = ""
    content_hash: str = ""
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class ApplicationLabSession(LabModel):
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    profile_id: str = ""
    master_resume_id: str = ""
    job_id: str = ""
    job_snapshot_id: str = ""
    current_step: int = Field(default=1, ge=1, le=10)
    status: ApplicationLabStatus = ApplicationLabStatus.DRAFT
    selected_context_refs: list[str] = Field(default_factory=list)
    analysis_run_ids: list[str] = Field(default_factory=list)
    readiness_report_id: str = ""
    resume_variant_id: str = ""
    application_kit_id: str = ""
    action_plan_id: str = ""
    tracker_application_id: str = ""
    invalidated_steps: list[int] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def normalize_progress(self) -> ApplicationLabSession:
        self.selected_context_refs = list(dict.fromkeys(filter(None, self.selected_context_refs)))
        self.analysis_run_ids = list(dict.fromkeys(filter(None, self.analysis_run_ids)))
        self.invalidated_steps = sorted(
            {step for step in self.invalidated_steps if 1 <= step <= 10}
        )
        return self


class ReadinessDimension(LabModel):
    dimension: str
    label: str
    status: Literal["met", "partial", "missing", "unknown", "not_applicable"]
    coverage: float | None = Field(default=None, ge=0, le=1)
    weight: float = Field(default=0, ge=0, le=1)
    evidence_count: int = Field(default=0, ge=0)
    explanation: str = ""


class ReadinessPerspective(LabModel):
    perspective_id: Literal["structure_ats", "narrative_positioning", "evidence_differentiators"]
    label: str
    summary: str
    findings: list[str] = Field(default_factory=list)


class ApplicationReadinessReport(LabModel):
    report_id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    readiness_score: float = Field(ge=0, le=100)
    score_explanation: str
    evidence_coverage: float = Field(ge=0, le=1)
    requirement_coverage: float = Field(ge=0, le=1)
    evidence_coverage_value: float | None = Field(default=None, ge=0, le=1)
    requirement_coverage_value: float | None = Field(default=None, ge=0, le=1)
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    risk_score: float = Field(default=0.0, ge=0, le=100)
    assessment_status: Literal["sufficient", "insufficient"] = "insufficient"
    unknown_dimension_count: int = Field(default=0, ge=0)
    source_dimensions: dict[str, ReadinessDimension] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    top_blockers: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    unsupported_claim_risks: list[str] = Field(default_factory=list)
    recommended_edits: list[str] = Field(default_factory=list)
    copy_ready_snippets: list[str] = Field(default_factory=list)
    action_plan_preview: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_used: list[str | dict[str, Any]] = Field(default_factory=list)
    perspectives: dict[str, ReadinessPerspective] = Field(default_factory=dict)
    dependency_hash: str = ""
    stale_reason: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ApplicationSuggestion(LabModel):
    suggestion_id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    suggestion_type: str
    section: str = ""
    before: str = ""
    after: str = ""
    reason: str = ""
    evidence_used: list[str | dict[str, Any]] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    status: SuggestionStatus = SuggestionStatus.PENDING
    edited_value: str = ""
    provider_run_id: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def require_evidence_for_claim(self) -> ApplicationSuggestion:
        claim_types = {"claim", "bullet", "summary", "project_description"}
        warning = "Sem evidência confirmada; não aceitar como fato."
        if (
            self.suggestion_type in claim_types
            and self.after.strip()
            and not self.evidence_used
            and warning not in self.warnings
        ):
            self.warnings.append(warning)
        return self


class ApplicationKitItem(LabModel):
    item_id: str = Field(default_factory=lambda: uuid4().hex)
    type: str
    content: str = ""
    evidence_used: list[str | dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provider_run_id: str = ""
    status: SuggestionStatus = SuggestionStatus.PENDING
    edited_content: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ApplicationKit(LabModel):
    application_kit_id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    title: str = "Kit de candidatura"
    items: list[ApplicationKitItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ActionPlanItem(LabModel):
    action_item_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    reason: str = ""
    priority: Literal["low", "medium", "high"] = "medium"
    due_at: datetime | None = None
    related_gap: str = ""
    related_evidence: list[str | dict[str, Any]] = Field(default_factory=list)
    estimated_effort: str = ""
    status: Literal["pending", "in_progress", "completed", "cancelled"] = "pending"
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class ApplicationActionPlan(LabModel):
    action_plan_id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    period_days: Literal[7, 14, 30] = 7
    title: str = "Plano de ação"
    items: list[ActionPlanItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "ActionPlanItem",
    "ApplicationActionPlan",
    "ApplicationKit",
    "ApplicationKitItem",
    "ApplicationLabSession",
    "ApplicationLabStatus",
    "ApplicationReadinessReport",
    "ApplicationSuggestion",
    "MasterResume",
    "ReadinessDimension",
    "ReadinessPerspective",
    "ResumeEntry",
    "ResumeExport",
    "ResumeSection",
    "ResumeTemplate",
    "ResumeVariant",
    "ResumeVariantChange",
    "SuggestionStatus",
    "utc_now",
]
