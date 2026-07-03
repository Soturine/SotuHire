"""Models for public exam and edital intelligence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

ExamConfidence = Literal["low", "medium", "high"]
ExamRequirementKind = Literal[
    "education",
    "degree",
    "professional_registry",
    "certification",
    "experience",
    "age",
    "nationality",
    "military_status",
    "electoral_status",
    "driver_license",
    "location",
    "availability",
    "document",
    "medical",
    "physical_test",
    "title_score",
    "other",
]
ExamRequirementStatus = Literal["matched", "missing", "uncertain"]
ExamRecommendation = Literal[
    "strong_fit",
    "good_fit",
    "review_requirements",
    "risky",
    "not_recommended",
    "insufficient_information",
]


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(UTC)


class ExamRequirement(BaseModel):
    """One requirement or document rule extracted from an edital."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(default_factory=lambda: uuid4().hex)
    kind: ExamRequirementKind = "other"
    description: str = Field(default="", max_length=2000)
    mandatory: bool = True
    evidence_needed: str = Field(default="", max_length=1000)
    matched_profile_item_ids: list[str] = Field(default_factory=list)
    match_status: ExamRequirementStatus = "uncertain"
    confidence: ExamConfidence = "medium"
    warnings: list[str] = Field(default_factory=list)


class ExamSubject(BaseModel):
    """One subject or syllabus group from a public exam notice."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="", max_length=240)
    topics: list[str] = Field(default_factory=list, max_length=120)
    weight: float | None = Field(default=None, ge=0)
    questions: int | None = Field(default=None, ge=0)
    stage: str = Field(default="", max_length=160)
    priority: str = Field(default="medium", max_length=40)
    source_excerpt: str = Field(default="", max_length=2000)


class ExamTimeline(BaseModel):
    """Important dates extracted from an edital."""

    model_config = ConfigDict(extra="forbid")

    registration_start: str = Field(default="", max_length=80)
    registration_end: str = Field(default="", max_length=80)
    payment_deadline: str = Field(default="", max_length=80)
    exam_date: str = Field(default="", max_length=80)
    result_date: str = Field(default="", max_length=80)
    appeal_deadlines: list[str] = Field(default_factory=list, max_length=40)
    document_submission_deadline: str = Field(default="", max_length=80)
    other_dates: list[str] = Field(default_factory=list, max_length=80)
    warnings: list[str] = Field(default_factory=list)


class ExamRole(BaseModel):
    """One role, position or public opportunity inside an edital."""

    model_config = ConfigDict(extra="forbid")

    role_id: str = Field(default_factory=lambda: uuid4().hex)
    notice_id: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=240)
    area: str = Field(default="", max_length=160)
    level: str = Field(default="", max_length=120)
    education_level: str = Field(default="", max_length=120)
    required_degree: str = Field(default="", max_length=240)
    required_registry: str = Field(default="", max_length=160)
    required_experience: str = Field(default="", max_length=500)
    required_certifications: list[str] = Field(default_factory=list, max_length=80)
    salary: str = Field(default="", max_length=160)
    workload: str = Field(default="", max_length=120)
    vacancies: str = Field(default="", max_length=120)
    reserved_vacancies: str = Field(default="", max_length=240)
    quota_notes: str = Field(default="", max_length=1000)
    contract_type: str = Field(default="public_exam", max_length=120)
    employment_regime: str = Field(default="", max_length=160)
    location: str = Field(default="", max_length=240)
    requirements: list[ExamRequirement] = Field(default_factory=list)
    subjects: list[ExamSubject] = Field(default_factory=list)
    stages: list[str] = Field(default_factory=list, max_length=80)


class ExamNotice(BaseModel):
    """A local, reviewable edital or public selection notice."""

    model_config = ConfigDict(extra="forbid")

    notice_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str = Field(default="", max_length=300)
    raw_text: str = Field(default="", max_length=500_000)
    source_url: str = Field(default="", max_length=2048)
    source_name: str = Field(default="", max_length=240)
    organization: str = Field(default="", max_length=240)
    exam_board: str = Field(default="", max_length=240)
    notice_number: str = Field(default="", max_length=160)
    publication_date: str = Field(default="", max_length=80)
    registration_fee: str = Field(default="", max_length=160)
    status: str = Field(default="draft", max_length=80)
    opportunity_type: str = Field(default="public_exam", max_length=80)
    locations: list[str] = Field(default_factory=list, max_length=80)
    roles: list[ExamRole] = Field(default_factory=list)
    timeline: ExamTimeline = Field(default_factory=ExamTimeline)
    documents: list[str] = Field(default_factory=list, max_length=120)
    general_requirements: list[ExamRequirement] = Field(default_factory=list)
    subjects: list[ExamSubject] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ExamFitScore(BaseModel):
    """Initial fit analysis between an edital role and the Universal Career Profile."""

    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(default=0, ge=0, le=100)
    requirement_score: int = Field(default=0, ge=0, le=100)
    timeline_score: int = Field(default=0, ge=0, le=100)
    location_score: int = Field(default=0, ge=0, le=100)
    salary_score: int = Field(default=0, ge=0, le=100)
    study_effort_score: int = Field(default=0, ge=0, le=100)
    profile_alignment_score: int = Field(default=0, ge=0, le=100)
    risk_score: int = Field(default=0, ge=0, le=100)
    recommendation: ExamRecommendation = "insufficient_information"
    matched_requirements: list[ExamRequirement] = Field(default_factory=list)
    missing_requirements: list[ExamRequirement] = Field(default_factory=list)
    uncertain_requirements: list[ExamRequirement] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StudyPlanDraft(BaseModel):
    """Small initial study plan draft; not a full study product."""

    model_config = ConfigDict(extra="forbid")

    days_until_exam: int | None = Field(default=None, ge=0)
    weekly_hours: int = Field(default=8, ge=1, le=80)
    subjects: list[ExamSubject] = Field(default_factory=list)
    priority_topics: list[str] = Field(default_factory=list, max_length=120)
    schedule_blocks: list[str] = Field(default_factory=list, max_length=120)
    warnings: list[str] = Field(default_factory=list)


class PublicExamImportInput(BaseModel):
    """Pasted edital import payload used by local parser and optional AI."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500_000)
    source_url: str = Field(default="", max_length=2048)
    source_name: str = Field(default="", max_length=240)
    use_ai: bool = False
    language: str = Field(default="pt-BR", max_length=20)


class PublicExamImportResult(BaseModel):
    """Review-only draft returned by public exam extraction."""

    model_config = ConfigDict(extra="forbid")

    notice: ExamNotice
    roles: list[ExamRole] = Field(default_factory=list)
    timeline: ExamTimeline = Field(default_factory=ExamTimeline)
    subjects: list[ExamSubject] = Field(default_factory=list)
    requirements: list[ExamRequirement] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    questions_to_confirm: list[str] = Field(default_factory=list)
    source_excerpts: list[str] = Field(default_factory=list)
    needs_user_review: bool = True
    provider_used: str = "local"
    requested_provider: str = "local"
    analysis_mode: str = "local"


class PublicExamListResult(BaseModel):
    """List response for persisted public exam notices."""

    model_config = ConfigDict(extra="forbid")

    notices: list[ExamNotice] = Field(default_factory=list)


class PublicExamConfirmResult(BaseModel):
    """Result of saving a reviewed notice."""

    model_config = ConfigDict(extra="forbid")

    notice: ExamNotice
    message: str = ""


class PublicExamAnalyzeResult(BaseModel):
    """Fit analysis response for one notice/role."""

    model_config = ConfigDict(extra="forbid")

    notice: ExamNotice
    role: ExamRole | None = None
    fit_score: ExamFitScore
    context_summary: str = ""
    checklist: list[ExamRequirement] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PublicExamStudyPlanResult(BaseModel):
    """Study plan response for one notice/role."""

    model_config = ConfigDict(extra="forbid")

    notice: ExamNotice
    role: ExamRole | None = None
    study_plan: StudyPlanDraft
    warnings: list[str] = Field(default_factory=list)
