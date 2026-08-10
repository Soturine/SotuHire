"""Reviewable interview, STAR, answer, and follow-up contracts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


InterviewType = Literal[
    "recruiter",
    "technical",
    "behavioral",
    "manager",
    "panel",
    "case",
    "academic",
    "public_sector",
    "other",
]
QuestionCategory = Literal[
    "behavioral",
    "technical",
    "role_specific",
    "company",
    "motivation",
    "gap",
    "salary",
    "availability",
    "leadership",
    "conflict",
    "project",
    "academic",
]


class InterviewSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(default_factory=lambda: uuid4().hex)
    application_id: str = ""
    job_snapshot_id: str = ""
    resume_snapshot_id: str = ""
    profile_id: str = ""
    evidence_scope_id: str = ""
    interview_type: InterviewType = "other"
    scheduled_at: datetime | None = None
    organization: str = ""
    role: str = ""
    status: Literal["draft", "scheduled", "preparing", "completed", "cancelled", "archived"] = (
        "draft"
    )
    notes: str = Field(default="", max_length=20_000)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class InterviewPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preparation_id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    opportunity_summary: str = ""
    critical_requirements: list[str] = Field(default_factory=list)
    confirmed_strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    likely_questions: list[str] = Field(default_factory=list)
    technical_questions: list[str] = Field(default_factory=list)
    behavioral_questions: list[str] = Field(default_factory=list)
    candidate_questions: list[str] = Field(default_factory=list)
    needs_confirmation: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    review_status: Literal["candidate", "reviewed", "rejected", "stale"] = "candidate"
    dependency_hash: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class StarStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str = Field(min_length=1, max_length=240)
    situation: str = Field(default="", max_length=10_000)
    task: str = Field(default="", max_length=10_000)
    action: str = Field(default="", max_length=10_000)
    result: str = Field(default="", max_length=10_000)
    skills: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    source_profile_item_ids: list[str] = Field(default_factory=list)
    review_status: Literal["candidate", "reviewed", "confirmed", "rejected", "stale"] = "candidate"
    tags: list[str] = Field(default_factory=list)
    generated_by: Literal["manual", "local", "ai"] = "manual"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def ai_numbers_require_evidence(self) -> StarStory:
        if self.generated_by == "ai" and re.search(r"\d", self.result) and not self.evidence_refs:
            raise ValueError("Resultados numericos estruturados por IA exigem evidencia.")
        return self


class InterviewQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str = ""
    category: QuestionCategory
    question: str = Field(min_length=1, max_length=2_000)
    rationale: str = Field(default="", max_length=5_000)
    evidence_refs: list[str] = Field(default_factory=list)
    review_status: Literal["candidate", "reviewed", "rejected"] = "candidate"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class InterviewDraftAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_id: str = Field(default_factory=lambda: uuid4().hex)
    question_id: str
    content: str = Field(default="", max_length=20_000)
    evidence_refs: list[str] = Field(default_factory=list)
    source_profile_item_ids: list[str] = Field(default_factory=list)
    status: Literal["draft", "reviewed", "rejected", "archived"] = "draft"
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def drafted_content_requires_evidence(self) -> InterviewDraftAnswer:
        if self.content.strip() and not (self.evidence_refs or self.source_profile_item_ids):
            raise ValueError("Respostas de entrevista precisam citar evidencia revisavel.")
        return self


class FollowUpDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    follow_up_id: str = Field(default_factory=lambda: uuid4().hex)
    application_id: str = ""
    interview_session_id: str = ""
    follow_up_type: Literal[
        "thank_you",
        "application_follow_up",
        "interview_follow_up",
        "status_request",
        "networking",
    ]
    subject: str = Field(default="", max_length=500)
    body: str = Field(default="", max_length=20_000)
    evidence_refs: list[str] = Field(default_factory=list)
    status: Literal["draft", "reviewed", "copied", "sent_manually", "archived"] = "draft"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "FollowUpDraft",
    "InterviewDraftAnswer",
    "InterviewPreparation",
    "InterviewQuestion",
    "InterviewSession",
    "InterviewType",
    "QuestionCategory",
    "StarStory",
]
