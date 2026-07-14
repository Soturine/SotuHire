"""Safe API contracts for AI quality, runs, benchmarks and feedback."""

from __future__ import annotations

from typing import Any

from modules.ai.feedback import AiDecision, AiFeedback, AiRating
from modules.storage.ai_runs import AiRun
from pydantic import BaseModel, ConfigDict, Field


class AiFeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    task_id: str
    rating: AiRating
    decision: AiDecision
    edited: bool = False
    unsupported_claim: bool = False
    comment: str = Field(default="", max_length=1000)
    request_id: str = ""

    def to_record(self) -> AiFeedback:
        return AiFeedback(**self.model_dump(exclude={"request_id"}))


class AiRunsPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AiRun]
    total: int
    limit: int
    offset: int


class AiFeedbackPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AiFeedback]
    limit: int
    offset: int


class AiQualitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executions: int = 0
    schema_validity: float | None = None
    fallback_rate: float | None = None
    average_latency_ms: float | None = None
    total_tokens: int = 0
    estimated_cost: float | None = None
    human_acceptance_rate: float | None = None
    human_edit_rate: float | None = None
    human_rejection_rate: float | None = None
    unsupported_claim_rate: float | None = None
    sample_confidence: str = "insufficient"
    empty_state: bool = True
    message: str = "Não há execuções suficientes para gerar métricas confiáveis."


class AiQualityCollection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[dict[str, Any]] = Field(default_factory=list)


__all__ = [
    "AiFeedbackCreate",
    "AiFeedbackPage",
    "AiQualityCollection",
    "AiQualitySummary",
    "AiRunsPage",
]
