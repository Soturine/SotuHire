"""Typed outcome events and aggregates."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

OutcomeEventType = Literal[
    "application_created",
    "application_submitted_manually",
    "response_received",
    "interview_scheduled",
    "interview_completed",
    "offer_received",
    "rejected",
    "withdrawn",
    "no_response",
]


class OutcomeEvent(BaseModel):
    """One explicitly recorded application event."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: uuid4().hex)
    application_id: str
    event_type: OutcomeEventType
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str = Field(default="", max_length=200)
    resume_variant_id: str = Field(default="", max_length=200)
    match_score: float | None = Field(default=None, ge=0, le=100)
    ats_score: float | None = Field(default=None, ge=0, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OutcomeRate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    numerator: int
    denominator: int
    sample_size: int
    confidence: Literal["insufficient", "indicative", "comparable"]
    note: str


class OutcomeGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    applications: int
    responses: int
    interviews: int
    offers: int
    response_rate: float
    confidence: Literal["insufficient", "indicative", "comparable"]


class ScoreOutcomeSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_size: int
    successful_average: float | None = None
    other_average: float | None = None
    confidence: Literal["insufficient", "indicative", "comparable"]
    note: str = "Associação exploratória; não demonstra causalidade."


class OutcomeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_size: int
    confidence: Literal["insufficient", "indicative", "comparable"]
    response_rate: OutcomeRate
    interview_rate: OutcomeRate
    offer_rate: OutcomeRate
    average_time_to_response_hours: float | None = None
    average_time_in_stage_hours: float | None = None
    source_effectiveness: list[OutcomeGroup] = Field(default_factory=list)
    resume_variant_effectiveness: list[OutcomeGroup] = Field(default_factory=list)
    match_score_vs_outcome: ScoreOutcomeSignal
    ats_score_vs_outcome: ScoreOutcomeSignal
    note: str = "Sinais exploratórios baseados em eventos manuais. Amostra e associação não demonstram causalidade."


__all__ = [
    "OutcomeEvent",
    "OutcomeEventType",
    "OutcomeGroup",
    "OutcomeRate",
    "OutcomeSummary",
    "ScoreOutcomeSignal",
]
