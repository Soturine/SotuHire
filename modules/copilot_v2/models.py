"""Strict contracts for the SotuHire v2 evidence and approval domains."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class EvidenceNodeType(StrEnum):
    PERSON = "person"
    PROFILE = "profile"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    PROJECT = "project"
    SKILL = "skill"
    KNOWLEDGE = "knowledge"
    TOOL = "tool"
    CERTIFICATION = "certification"
    PROFESSIONAL_REGISTRATION = "professional_registration"
    PUBLICATION = "publication"
    RESEARCH = "research"
    COURSE = "course"
    AWARD = "award"
    EVENT = "event"
    VOLUNTEERING = "volunteering"
    EXTENSION_ACTIVITY = "extension_activity"
    TEACHING = "teaching"
    PORTFOLIO_ITEM = "portfolio_item"
    REPOSITORY = "repository"
    DOCUMENT = "document"
    OPPORTUNITY = "opportunity"
    REQUIREMENT = "requirement"
    APPLICATION = "application"
    INTERVIEW = "interview"
    OUTCOME = "outcome"
    CAREER_GOAL = "career_goal"


class EvidenceRelationType(StrEnum):
    EXPERIENCE_DEMONSTRATES_SKILL = "experience_demonstrates_skill"
    PROJECT_DEMONSTRATES_SKILL = "project_demonstrates_skill"
    PROJECT_USES_TOOL = "project_uses_tool"
    PUBLICATION_RELATES_TO_TOPIC = "publication_relates_to_topic"
    EDUCATION_SUPPORTS_KNOWLEDGE = "education_supports_knowledge"
    CERTIFICATION_SUPPORTS_SKILL = "certification_supports_skill"
    REGISTRATION_AUTHORIZES_ROLE = "registration_authorizes_role"
    PORTFOLIO_ITEM_EVIDENCES_PROJECT = "portfolio_item_evidences_project"
    REQUIREMENT_REQUIRES_SKILL = "requirement_requires_skill"
    OPPORTUNITY_REQUIRES_REQUIREMENT = "opportunity_requires_requirement"
    STAR_STORY_DERIVED_FROM_EXPERIENCE = "star_story_derived_from_experience"
    APPLICATION_USED_RESUME = "application_used_resume"
    OUTCOME_ASSOCIATED_WITH_APPLICATION = "outcome_associated_with_application"


class ReviewStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    STALE = "stale"


class EvidenceNode(StrictModel):
    node_id: str = Field(min_length=1, max_length=128)
    node_type: EvidenceNodeType
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(default="", max_length=10_000)
    payload: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list, max_length=100)
    review_status: ReviewStatus = ReviewStatus.CANDIDATE
    confidence: float = Field(default=0, ge=0, le=1)
    sensitive: bool = False
    created_at: datetime
    updated_at: datetime
    stale_at: datetime | None = None


class EvidenceEdge(StrictModel):
    edge_id: str = Field(min_length=1, max_length=128)
    source_id: str
    target_id: str
    relation_type: EvidenceRelationType
    evidence_refs: list[str] = Field(default_factory=list, max_length=100)
    source_refs: list[str] = Field(default_factory=list, max_length=100)
    review_status: ReviewStatus = ReviewStatus.CANDIDATE
    confidence: float = Field(default=0, ge=0, le=1)
    created_at: datetime
    updated_at: datetime
    stale_at: datetime | None = None

    @model_validator(mode="after")
    def prevent_self_edge(self) -> EvidenceEdge:
        if self.source_id == self.target_id:
            raise ValueError("Evidence edges cannot point to the same node")
        return self


class PortfolioType(StrEnum):
    SOFTWARE = "software"
    ENGINEERING = "engineering"
    DESIGN = "design"
    RESEARCH = "research"
    PUBLICATION = "publication"
    TEACHING = "teaching"
    CASE_STUDY = "case_study"
    PRESENTATION = "presentation"
    VIDEO = "video"
    AUDIO = "audio"
    WRITING = "writing"
    VISUAL_ART = "visual_art"
    ARCHITECTURE = "architecture"
    DATA = "data"
    ELECTRONICS = "electronics"
    HARDWARE = "hardware"
    ACADEMIC = "academic"
    VOLUNTEERING = "volunteering"
    CUSTOM = "custom"


class PortfolioAttachment(StrictModel):
    attachment_id: str
    name: str = Field(min_length=1, max_length=240)
    media_type: str = Field(max_length=120)
    local_path: str = Field(default="", max_length=1_024)
    size_bytes: int = Field(default=0, ge=0, le=50 * 1024 * 1024)
    sha256: str = Field(default="", pattern=r"^[a-f0-9]{64}$|^$")


class PortfolioItem(StrictModel):
    portfolio_item_id: str
    title: str = Field(min_length=1, max_length=240)
    type: PortfolioType
    description: str = Field(default="", max_length=20_000)
    role: str = Field(default="", max_length=240)
    start_date: str | None = None
    end_date: str | None = None
    links: list[HttpUrl] = Field(default_factory=list, max_length=20)
    attachments: list[PortfolioAttachment] = Field(default_factory=list, max_length=50)
    skills: list[str] = Field(default_factory=list, max_length=100)
    tools: list[str] = Field(default_factory=list, max_length=100)
    evidence_refs: list[str] = Field(default_factory=list, max_length=100)
    source_refs: list[str] = Field(default_factory=list, max_length=100)
    review_status: ReviewStatus = ReviewStatus.CANDIDATE
    visibility: str = Field(default="private", pattern="^(private|exportable|public-link)$")
    created_at: datetime
    updated_at: datetime
    stale_at: datetime | None = None


class ProfessionalRegistration(StrictModel):
    type: str
    council: str
    registration_number: str
    jurisdiction: str = ""
    status: str = ""
    issue_date: str | None = None
    expiry_date: str | None = None
    source: str = "manual"
    confirmed: bool = False
    sensitive: bool = True


class NextBestAction(StrictModel):
    action_id: str
    type: str
    priority: int = Field(ge=0, le=100)
    urgency: str = Field(pattern="^(low|medium|high|critical)$")
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)
    related_entities: list[str] = Field(default_factory=list)
    impact: str
    estimated_effort: str
    blocking: bool = False
    created_at: datetime
    expires_at: datetime | None = None


class ConfidenceBreakdown(StrictModel):
    data_coverage: float = Field(ge=0, le=1)
    rule_confidence: float = Field(ge=0, le=1)
    provider_confidence: float | None = Field(default=None, ge=0, le=1)


class CareerState(StrictModel):
    profile_summary: str = ""
    career_goals: list[str] = Field(default_factory=list)
    current_focus: list[str] = Field(default_factory=list)
    confirmed_strengths: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    portfolio_gaps: list[str] = Field(default_factory=list)
    academic_strengths: list[str] = Field(default_factory=list)
    professional_constraints: list[str] = Field(default_factory=list)
    active_applications: int = 0
    upcoming_interviews: int = 0
    pending_followups: int = 0
    overdue_tasks: int = 0
    stale_artifacts: int = 0
    top_opportunities: list[dict[str, Any]] = Field(default_factory=list)
    recent_outcomes: list[dict[str, Any]] = Field(default_factory=list)
    provider_health: str = "unknown"
    data_health: str = "healthy"
    recommendation_candidates: list[NextBestAction] = Field(default_factory=list)
    confidence: ConfidenceBreakdown
    dependency_hash: str
    generated_at: datetime


class ProposalStatus(StrEnum):
    PROPOSED = "proposed"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    UNDONE = "undone"
    EXPIRED = "expired"
    STALE = "stale"


class ProposedAction(StrictModel):
    proposal_id: str
    action_type: str
    title: str
    description: str = ""
    reason: str
    source: str
    evidence_refs: list[str] = Field(default_factory=list)
    affected_entities: list[str] = Field(default_factory=list)
    before_snapshot: dict[str, Any] = Field(default_factory=dict)
    after_preview: dict[str, Any] = Field(default_factory=dict)
    risk: str = Field(default="low", pattern="^(low|medium|high)$")
    reversible: bool = False
    undo_strategy: str = ""
    status: ProposalStatus = ProposalStatus.PROPOSED
    dependency_hash: str = ""
    idempotency_key: str
    created_at: datetime
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    rejected_at: datetime | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def require_undo_strategy(self) -> ProposedAction:
        if self.reversible and not self.undo_strategy.strip():
            raise ValueError("Reversible proposals require an undo strategy")
        return self


class CopilotPlanStep(StrictModel):
    step_id: str
    position: int = Field(ge=0)
    title: str
    status: str = "pending"
    proposal_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class CopilotPlan(StrictModel):
    plan_id: str
    intent: str
    title: str
    status: str = "draft"
    context_summary: dict[str, Any] = Field(default_factory=dict)
    steps: list[CopilotPlanStep] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CopilotContextReceipt(StrictModel):
    purpose: str
    item_count: int = Field(ge=0)
    token_estimate: int = Field(ge=0)
    external_share: bool = False
    omitted_sensitive_items: int = Field(default=0, ge=0)
