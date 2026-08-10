"""Strict structured outputs for career intelligence and action workflows."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from modules.ai.schemas.common import StrictSchema


class EvidenceBoundOutput(StrictSchema):
    evidence_refs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    needs_user_review: bool = True


class InterviewQuestionCandidate(StrictSchema):
    category: str = "role_specific"
    question: str = ""
    rationale: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class InterviewQuestionGenerationOutput(EvidenceBoundOutput):
    questions: list[InterviewQuestionCandidate] = Field(default_factory=list)
    questions_for_candidate: list[str] = Field(default_factory=list)


class InterviewAnswerDraftingOutput(EvidenceBoundOutput):
    draft: str = ""
    missing_information: list[str] = Field(default_factory=list)


class StarStoryStructuringOutput(EvidenceBoundOutput):
    title: str = ""
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    skills: list[str] = Field(default_factory=list)


class FollowUpDraftingOutput(EvidenceBoundOutput):
    follow_up_type: str = "status_request"
    subject: str = ""
    body: str = ""
    status: Literal["draft"] = "draft"


class CareerPlanExplanationOutput(EvidenceBoundOutput):
    explanation: str = ""
    priorities: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)


class CertificationRecommendationExplanationOutput(EvidenceBoundOutput):
    recommendation_name: str = ""
    classification: Literal[
        "required", "commonly_requested", "useful", "optional", "low_priority"
    ] = "optional"
    explanation: str = ""
    official_source_needed: bool = True


class ProjectGapRecommendationOutput(EvidenceBoundOutput):
    gap: str = ""
    objective: str = ""
    deliverables: list[str] = Field(default_factory=list)
    evidence_to_produce: list[str] = Field(default_factory=list)
    effort_estimate: str = ""
    skills: list[str] = Field(default_factory=list)


class OpportunityEnrichmentOutput(EvidenceBoundOutput):
    summary: str = ""
    occupation_candidates: list[str] = Field(default_factory=list)
    skill_candidates: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    source_quality_notes: list[str] = Field(default_factory=list)


class TaxonomyMappingExplanationOutput(EvidenceBoundOutput):
    source_text: str = ""
    target_label: str = ""
    taxonomy_ref: str = ""
    match_method: str = "semantic_candidate"
    confidence: float = Field(default=0.0, ge=0, le=1)
    review_status: Literal["candidate"] = "candidate"


__all__ = [
    "CareerPlanExplanationOutput",
    "CertificationRecommendationExplanationOutput",
    "FollowUpDraftingOutput",
    "InterviewAnswerDraftingOutput",
    "InterviewQuestionGenerationOutput",
    "OpportunityEnrichmentOutput",
    "ProjectGapRecommendationOutput",
    "StarStoryStructuringOutput",
    "TaxonomyMappingExplanationOutput",
]
