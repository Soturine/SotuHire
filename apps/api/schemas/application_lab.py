"""HTTP contracts for Application Lab and Resume Studio."""

from __future__ import annotations

from typing import Any, Literal

from modules.application_lab.models import (
    ApplicationActionPlan,
    ApplicationAnalysisBundle,
    ApplicationKit,
    ApplicationKitItem,
    ApplicationLabSession,
    ApplicationLabStatus,
    ApplicationReadinessReport,
    ApplicationSuggestion,
    MasterResume,
    ResumeExport,
    ResumeSection,
    ResumeTemplate,
    ResumeVariant,
)
from modules.parsers.document_ingestion import IngestedDocument
from pydantic import BaseModel, ConfigDict, Field


class LabApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaginationMeta(LabApiModel):
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)
    has_more: bool = False


class ApplicationLabSessionCreateRequest(LabApiModel):
    profile_id: str = Field(default="", max_length=200)
    master_resume_id: str = Field(default="", max_length=200)
    job_id: str = Field(default="", max_length=200)
    job_snapshot_id: str = Field(default="", max_length=200)
    selected_context_refs: list[str] = Field(default_factory=list, max_length=500)
    request_id: str = Field(default="", max_length=120)


class ApplicationLabSessionUpdateRequest(LabApiModel):
    profile_id: str | None = Field(default=None, max_length=200)
    master_resume_id: str | None = Field(default=None, max_length=200)
    job_id: str | None = Field(default=None, max_length=200)
    job_snapshot_id: str | None = Field(default=None, max_length=200)
    current_step: int | None = Field(default=None, ge=1, le=10)
    status: ApplicationLabStatus | None = None
    selected_context_refs: list[str] | None = Field(default=None, max_length=500)
    request_id: str = Field(default="", max_length=120)


class ApplicationLabSessionPage(LabApiModel):
    items: list[ApplicationLabSession]
    pagination: PaginationMeta


class ApplicationLabSessionDetail(LabApiModel):
    session: ApplicationLabSession
    analysis_bundle: ApplicationAnalysisBundle | None = None
    report: ApplicationReadinessReport | None = None
    suggestions: list[ApplicationSuggestion] = Field(default_factory=list)
    variant: ResumeVariant | None = None
    kit: ApplicationKit | None = None
    action_plan: ApplicationActionPlan | None = None


class ApplicationLabAnalyzeResponse(ApplicationLabSessionDetail):
    analysis_snapshot_id: str
    analysis_snapshot_ids: dict[str, str] = Field(default_factory=dict)
    progress_steps: list[str] = Field(default_factory=list)


class SuggestionEditRequest(LabApiModel):
    edited_value: str = Field(min_length=1, max_length=20_000)
    request_id: str = Field(default="", max_length=120)


class RequestMetadata(LabApiModel):
    request_id: str = Field(default="", max_length=120)


class VariantFromSessionRequest(RequestMetadata):
    title: str = Field(default="", max_length=240)


class ActionPlanCreateRequest(RequestMetadata):
    period_days: Literal[7, 14, 30] = 7


class TrackerSaveRequest(RequestMetadata):
    privacy_acknowledged: bool = False
    source_capture_id: str = Field(default="", max_length=200)


class TrackerSaveResponse(LabApiModel):
    tracker_application_id: str
    session: ApplicationLabSession


class ApplicationKitResponse(LabApiModel):
    kit: ApplicationKit
    snapshot_id: str


class ApplicationKitItemReviewRequest(LabApiModel):
    status: Literal["pending", "accepted", "edited", "rejected", "stale"]
    edited_content: str = Field(default="", max_length=100_000)
    request_id: str = Field(default="", max_length=120)


class ApplicationKitItemResponse(LabApiModel):
    item: ApplicationKitItem


class ApplicationKitExportResponse(LabApiModel):
    application_kit_id: str
    items: dict[str, str] = Field(default_factory=dict)


class MasterResumeUpsertRequest(LabApiModel):
    resume: MasterResume
    request_id: str = Field(default="", max_length=120)


class MasterResumeResponse(LabApiModel):
    resume: MasterResume


class ResumeIngestionRequest(LabApiModel):
    file_name: str = Field(min_length=1, max_length=240)
    content_base64: str = Field(min_length=1, max_length=14_000_000)
    request_id: str = Field(default="", max_length=120)


class ResumeIngestionResponse(LabApiModel):
    document: IngestedDocument
    master_resume_draft: MasterResume


class ResumeVariantPage(LabApiModel):
    items: list[ResumeVariant]
    pagination: PaginationMeta


class ResumeVariantCreateRequest(LabApiModel):
    variant: ResumeVariant
    request_id: str = Field(default="", max_length=120)


class ResumeVariantUpdateRequest(LabApiModel):
    title: str | None = Field(default=None, max_length=240)
    target_role: str | None = Field(default=None, max_length=240)
    sections: list[ResumeSection] | None = None
    validation_warnings: list[str] | None = Field(default=None, max_length=100)
    request_id: str = Field(default="", max_length=120)


class ResumeVariantResponse(LabApiModel):
    variant: ResumeVariant


class ResumeTemplatesResponse(LabApiModel):
    items: list[ResumeTemplate]


class ResumeExportRequest(LabApiModel):
    format: Literal["json_resume", "pdf", "docx"] = "json_resume"
    template_id: str = Field(default="classic", max_length=100)
    page_size: Literal["A4", "Letter"] = "A4"
    request_id: str = Field(default="", max_length=120)


class ResumeExportResponse(LabApiModel):
    export: ResumeExport
    payload: dict[str, Any] | None = None


__all__ = [
    "ActionPlanCreateRequest",
    "ApplicationKitResponse",
    "ApplicationKitExportResponse",
    "ApplicationKitItemResponse",
    "ApplicationKitItemReviewRequest",
    "ApplicationLabAnalyzeResponse",
    "ApplicationLabSessionCreateRequest",
    "ApplicationLabSessionDetail",
    "ApplicationLabSessionPage",
    "ApplicationLabSessionUpdateRequest",
    "MasterResumeResponse",
    "MasterResumeUpsertRequest",
    "PaginationMeta",
    "RequestMetadata",
    "ResumeExportRequest",
    "ResumeExportResponse",
    "ResumeIngestionRequest",
    "ResumeIngestionResponse",
    "ResumeTemplatesResponse",
    "ResumeVariantCreateRequest",
    "ResumeVariantPage",
    "ResumeVariantResponse",
    "ResumeVariantUpdateRequest",
    "SuggestionEditRequest",
    "TrackerSaveRequest",
    "TrackerSaveResponse",
    "VariantFromSessionRequest",
]
