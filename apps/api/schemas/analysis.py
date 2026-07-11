"""Endpoint-specific DTOs for extraction and analysis flows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from modules.context import CareerContextEvidence
from modules.core.collection_method import CollectionMethod
from modules.github_analyzer.repository_models import RepositoryAnalysisInput
from modules.github_analyzer.schemas import GitHubAnalyzerReport
from modules.portfolio.schemas import ProjectAnalysisPayload
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.job_posting import JobPostingSchema
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.schemas.resume_tailor import ResumeTailorOutput
from modules.schemas.user_preferences import UserPreferences
from modules.storage.models import StoredAnalysis
from modules.tracker.dashboard import DashboardMetrics
from modules.tracker.status import JobStatus
from pydantic import BaseModel, ConfigDict, Field


class AiTraceMetadata(BaseModel):
    """Flat, backwards-compatible trace metadata for one analysis execution."""

    model_config = ConfigDict(extra="forbid")

    provider_requested: str = "local"
    requested_provider: str = "local"
    provider_used: str = "local"
    model_requested: str = "local"
    model_used: str = "local"
    model: str = ""
    prompt_id: str = ""
    prompt_version: str = ""
    analysis_mode: Literal["local", "ai", "fallback"] = "local"
    fallback_used: bool = False
    fallback_reason: str = ""
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str = ""
    source_refs: list[str] = Field(default_factory=list)
    evidence_used: list[CareerContextEvidence] = Field(default_factory=list)
    needs_user_review: bool = True


class ResumeExtractRequest(BaseModel):
    """Extract a structured resume profile from pasted text."""

    model_config = ConfigDict(extra="forbid")

    resume_text: str = Field(min_length=1, max_length=200_000)
    source_type: str = Field(default="text", max_length=50)
    request_id: str = Field(default="", max_length=120)
    include_raw_text: bool = False


class ResumeExtractResponse(AiTraceMetadata):
    """Structured resume extraction response."""

    model_config = ConfigDict(extra="forbid")

    profile: ResumeProfileSchema
    confidence: float = Field(ge=0, le=1)
    low_confidence_fields: list[str] = Field(default_factory=list)


class JobExtractRequest(BaseModel):
    """Extract a structured job posting from pasted text."""

    model_config = ConfigDict(extra="forbid")

    job_text: str = Field(min_length=1, max_length=200_000)
    source_url: str = Field(default="", max_length=2048)
    request_id: str = Field(default="", max_length=120)
    include_raw_text: bool = False


class JobExtractResponse(AiTraceMetadata):
    """Structured job extraction response."""

    model_config = ConfigDict(extra="forbid")

    job: JobPostingSchema
    confidence: float = Field(ge=0, le=1)
    low_confidence_fields: list[str] = Field(default_factory=list)


class MatchAnalyzeRequest(BaseModel):
    """Analyze resume and job fit with the existing match engine."""

    model_config = ConfigDict(extra="forbid")

    resume_text: str = Field(default="", max_length=200_000)
    job_text: str = Field(default="", max_length=200_000)
    profile: ResumeProfileSchema | None = None
    job: JobPostingSchema | None = None
    preferences: UserPreferences | None = None
    github_evidence: list[str] = Field(default_factory=list, max_length=100)
    portfolio_evidence: list[str] = Field(default_factory=list, max_length=100)
    request_id: str = Field(default="", max_length=120)


class MatchAnalyzeResponse(AiTraceMetadata):
    """Match analysis plus small API metadata."""

    model_config = ConfigDict(extra="forbid")

    analysis: JobAnalysisSchema
    local_first: bool = True
    memory_shared_with_provider: bool = False
    context_summary: str = ""
    context_evidence_count: int = 0
    context_warnings: list[str] = Field(default_factory=list)


class AtsAnalyzeRequest(BaseModel):
    """Review ATS keywords without turning missing evidence into claims."""

    model_config = ConfigDict(extra="forbid")

    job_keywords: list[str] = Field(default_factory=list, max_length=100)
    match_analysis: JobAnalysisSchema | None = None
    resume_text: str = Field(default="", max_length=200_000)
    job_text: str = Field(default="", max_length=200_000)
    request_id: str = Field(default="", max_length=120)


class AtsAnalyzeResponse(AiTraceMetadata):
    """ATS keyword review response."""

    model_config = ConfigDict(extra="forbid")

    ats_score: int = Field(ge=0, le=100)
    present: list[str] = Field(default_factory=list)
    missing_but_safe_to_add_if_true: list[str] = Field(default_factory=list)
    missing_without_evidence: list[str] = Field(default_factory=list)
    ai_insights: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    context_summary: str = ""
    context_evidence_keywords: list[str] = Field(default_factory=list)
    safe_keywords_from_context: list[str] = Field(default_factory=list)
    keywords_without_context_evidence: list[str] = Field(default_factory=list)
    profile_or_rag_terms: list[str] = Field(default_factory=list)
    unevidenced_profile_claims: list[str] = Field(default_factory=list)


class ResumeTailorRequest(BaseModel):
    """Build safe resume-tailoring suggestions."""

    model_config = ConfigDict(extra="forbid")

    target_role: str = Field(min_length=1, max_length=200)
    job_text: str = Field(default="", max_length=200_000)
    evidence_text: str = Field(default="", max_length=200_000)
    target_company: str | None = Field(default=None, max_length=200)
    match_analysis: JobAnalysisSchema | None = None
    request_id: str = Field(default="", max_length=120)


class ResumeTailorResponse(AiTraceMetadata):
    """Safe tailoring output wrapper."""

    model_config = ConfigDict(extra="forbid")

    tailor: ResumeTailorOutput
    safe_to_export: bool = False
    ai_suggestions: list[str] = Field(default_factory=list)
    context_summary: str = ""
    context_evidence_count: int = 0


class GitHubRepoAnalyzeRequest(BaseModel):
    """Analyze a public GitHub repository as career evidence."""

    model_config = ConfigDict(extra="forbid")

    repo_url: str = Field(min_length=1, max_length=2048)
    mode: Literal[
        "technical_quality",
        "portfolio_value",
        "resume_evidence",
        "job_alignment",
        "full",
    ] = "full"
    target_role: str = Field(default="", max_length=200)
    target_job: dict[str, object] = Field(default_factory=dict)
    candidate_profile: dict[str, object] = Field(default_factory=dict)
    career_domains: list[str] = Field(default_factory=list, max_length=50)
    language: str = Field(default="pt-BR", max_length=20)
    fallback_payload: ProjectAnalysisPayload | None = None
    request_id: str = Field(default="", max_length=120)

    def to_analysis_input(self) -> RepositoryAnalysisInput:
        """Convert transport fields to the core analyzer context."""
        return RepositoryAnalysisInput(
            mode=self.mode,
            target_role=self.target_role,
            target_job=self.target_job,
            candidate_profile=self.candidate_profile,
            career_domains=self.career_domains,
            language=self.language,
        )


class GitHubRepoAnalyzeResponse(AiTraceMetadata):
    """GitHub analyzer response wrapper."""

    model_config = ConfigDict(extra="forbid")

    report: GitHubAnalyzerReport
    profile_evidence_candidates: list[CareerContextEvidence] = Field(default_factory=list)


class TrackerJobCreateRequest(BaseModel):
    """Create or upsert a tracker job card."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=300)
    company: str = Field(default="", max_length=200)
    source_url: str = Field(default="", max_length=2048)
    modality: str = Field(default="", max_length=80)
    seniority: str = Field(default="", max_length=80)
    requirements: list[str] = Field(default_factory=list, max_length=100)
    status: JobStatus = JobStatus.FOUND
    match_score: int = Field(default=0, ge=0, le=100)
    ats_score: int = Field(default=0, ge=0, le=100)
    opportunity_fit_score: int = Field(default=0, ge=0, le=100)
    risk_score: int = Field(default=0, ge=0, le=100)
    recommendation: Literal["apply", "apply_with_adjustments", "save_for_later", "ignore"] = (
        "save_for_later"
    )
    collection_method: CollectionMethod = "manual_url"
    notes: str = Field(default="", max_length=10_000)
    privacy_acknowledged: bool = True
    request_id: str = Field(default="", max_length=120)


class TrackerJobUpdateRequest(BaseModel):
    """Update user-controlled fields on a tracker card."""

    model_config = ConfigDict(extra="forbid")

    status: JobStatus | None = None
    notes: str | None = Field(default=None, max_length=10_000)
    request_id: str = Field(default="", max_length=120)


class TrackerJobContext(BaseModel):
    """Context hints for one tracker card."""

    model_config = ConfigDict(extra="forbid")

    context_summary: str = ""
    fit_reason: str = ""
    next_action_hint: str = ""
    aligned_with_profile: bool | None = None
    recurring_gaps: list[str] = Field(default_factory=list)


class TrackerJobResponse(TrackerJobContext):
    """Tracker card response."""

    job: StoredAnalysis


class TrackerJobsResponse(BaseModel):
    """Tracker list response."""

    model_config = ConfigDict(extra="forbid")

    jobs: list[StoredAnalysis] = Field(default_factory=list)
    context_summary: str = ""
    job_contexts: dict[str, TrackerJobContext] = Field(default_factory=dict)


class TrackerMetricsResponse(BaseModel):
    """Tracker KPI response."""

    model_config = ConfigDict(extra="forbid")

    metrics: DashboardMetrics
    total_saved: int = 0
    total_applied: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    average_match_by_status: dict[str, float] = Field(default_factory=dict)
    response_rate: float = 0
    interview_rate: float = 0
    offer_rate: float = 0


class RequirementRankItem(BaseModel):
    """Ranked requirement item for frontend charts."""

    model_config = ConfigDict(extra="forbid")

    name: str
    count: int
    status_scope: str = ""
    sources: list[str] = Field(default_factory=list)
    candidate_has_evidence: bool = False


class CriticalGapItem(BaseModel):
    """Repeated gap or missing requirement."""

    model_config = ConfigDict(extra="forbid")

    name: str
    count: int
    severity: Literal["low", "medium", "high"] = "medium"
    safe_action: str = ""


class RequirementBySourceItem(BaseModel):
    """Requirement count grouped by source."""

    model_config = ConfigDict(extra="forbid")

    source: str
    requirement: str
    count: int


class TrackerRequirementsResponse(BaseModel):
    """Application Intelligence requirements response."""

    model_config = ConfigDict(extra="forbid")

    top_requirements: list[RequirementRankItem] = Field(default_factory=list)
    missing_requirements: list[CriticalGapItem] = Field(default_factory=list)
    critical_gaps: list[CriticalGapItem] = Field(default_factory=list)
    requirements_by_source: list[RequirementBySourceItem] = Field(default_factory=list)


class FunnelStage(BaseModel):
    """Single funnel stage."""

    model_config = ConfigDict(extra="forbid")

    status: str
    label: str
    count: int


class FunnelConversion(BaseModel):
    """Conversion rate between two funnel stages."""

    model_config = ConfigDict(extra="forbid")

    from_status: str = Field(serialization_alias="from")
    to_status: str = Field(serialization_alias="to")
    rate: float


class TrackerFunnelResponse(BaseModel):
    """Tracker funnel response."""

    model_config = ConfigDict(extra="forbid")

    stages: list[FunnelStage] = Field(default_factory=list)
    conversion_rates: list[FunnelConversion] = Field(default_factory=list)


class SourceMetricsItem(BaseModel):
    """Metrics grouped by source/domain."""

    model_config = ConfigDict(extra="forbid")

    name: str
    saved: int = 0
    applied: int = 0
    interviews: int = 0
    average_match: float = 0
    top_requirements: list[str] = Field(default_factory=list)


class TrackerSourcesResponse(BaseModel):
    """Source comparison response."""

    model_config = ConfigDict(extra="forbid")

    sources: list[SourceMetricsItem] = Field(default_factory=list)
