"""DTOs for public exams and edital endpoints."""

from __future__ import annotations

from modules.public_exams import (
    ExamNotice,
    PublicExamAnalyzeResult,
    PublicExamConfirmResult,
    PublicExamImportResult,
    PublicExamListResult,
    PublicExamStudyPlanResult,
)
from pydantic import BaseModel, ConfigDict, Field


class PublicExamImportRequest(BaseModel):
    """Import one pasted edital as a review-only draft."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500_000)
    source_url: str = Field(default="", max_length=2048)
    source_name: str = Field(default="", max_length=240)
    use_ai: bool = False
    language: str = Field(default="pt-BR", max_length=20)
    request_id: str = Field(default="", max_length=120)


class PublicExamConfirmRequest(BaseModel):
    """Persist one reviewed edital notice."""

    model_config = ConfigDict(extra="forbid")

    notice: ExamNotice
    request_id: str = Field(default="", max_length=120)


class PublicExamAnalyzeRequest(BaseModel):
    """Analyze one role against the Universal Career Profile."""

    model_config = ConfigDict(extra="forbid")

    role_id: str = Field(default="", max_length=120)
    request_id: str = Field(default="", max_length=120)


class PublicExamStudyPlanRequest(BaseModel):
    """Generate a small initial study plan."""

    model_config = ConfigDict(extra="forbid")

    role_id: str = Field(default="", max_length=120)
    weekly_hours: int = Field(default=8, ge=1, le=80)
    request_id: str = Field(default="", max_length=120)


class PublicExamImportResponse(PublicExamImportResult):
    """Public exam import response."""


class PublicExamListResponse(PublicExamListResult):
    """Saved notices response."""


class PublicExamConfirmResponse(PublicExamConfirmResult):
    """Saved notice response."""


class PublicExamAnalyzeResponse(PublicExamAnalyzeResult):
    """Fit analysis response."""


class PublicExamStudyPlanResponse(PublicExamStudyPlanResult):
    """Study plan response."""
