"""Tasks, reminders, plans, certifications, and gap-project contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class CareerTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(default_factory=lambda: uuid4().hex)
    task_type: Literal[
        "follow_up",
        "interview",
        "application",
        "document",
        "certification",
        "project",
        "study",
        "networking",
        "custom",
    ] = "custom"
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=10_000)
    status: Literal["pending", "in_progress", "completed", "cancelled", "archived"] = "pending"
    priority: Literal["low", "medium", "high"] = "medium"
    due_at: datetime | None = None
    related_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class Reminder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reminder_id: str = Field(default_factory=lambda: uuid4().hex)
    task_id: str = ""
    remind_at: datetime
    title: str = Field(min_length=1, max_length=300)
    status: Literal["scheduled", "shown", "dismissed", "cancelled"] = "scheduled"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CareerAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    rationale: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    status: Literal["planned", "in_progress", "completed", "cancelled"] = "planned"
    due_at: datetime | None = None


class CareerGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    horizon: Literal["30_days", "90_days", "6_months", "1_year"]
    success_criteria: list[str] = Field(default_factory=list)
    actions: list[CareerAction] = Field(default_factory=list)


class CertificationRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    classification: Literal["required", "commonly_requested", "useful", "optional", "low_priority"]
    rationale: str = ""
    official_source_url: str = ""
    source_status: Literal["official", "needs_source", "not_available"] = "needs_source"
    review_status: Literal["candidate", "reviewed", "rejected"] = "candidate"


class GapProject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(default_factory=lambda: uuid4().hex)
    domain: str
    gap: str
    objective: str
    deliverables: list[str] = Field(default_factory=list)
    evidence_to_produce: list[str] = Field(default_factory=list)
    effort_estimate: str = ""
    skills: list[str] = Field(default_factory=list)
    review_status: Literal["candidate", "reviewed", "accepted", "rejected"] = "candidate"


class CareerPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(default_factory=lambda: uuid4().hex)
    profile_id: str = ""
    title: str = Field(min_length=1, max_length=300)
    status: Literal["draft", "active", "completed", "archived", "stale"] = "draft"
    goals: list[CareerGoal] = Field(default_factory=list)
    certifications: list[CertificationRecommendation] = Field(default_factory=list)
    gap_projects: list[GapProject] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    dependency_hash: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "CareerAction",
    "CareerGoal",
    "CareerPlan",
    "CareerTask",
    "CertificationRecommendation",
    "GapProject",
    "Reminder",
]
