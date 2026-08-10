"""Registered provider consumer with conservative local fallbacks for SotuHire v2.0."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.provider_errors import sanitize_provider_message
from modules.ai.schemas.career_workflows import (
    CareerPlanExplanationOutput,
    CertificationRecommendationExplanationOutput,
    FollowUpDraftingOutput,
    InterviewAnswerDraftingOutput,
    InterviewQuestionGenerationOutput,
    OpportunityEnrichmentOutput,
    ProjectGapRecommendationOutput,
    StarStoryStructuringOutput,
    TaxonomyMappingExplanationOutput,
)
from modules.ai.task_registry import default_ai_task_registry
from modules.ai.tracing import record_ai_run

CareerWorkflowTask = Literal[
    "interview_question_generation",
    "interview_answer_drafting",
    "star_story_structuring",
    "follow_up_drafting",
    "career_plan_explanation",
    "certification_recommendation_explanation",
    "project_gap_recommendation",
    "opportunity_enrichment",
    "taxonomy_mapping_explanation",
]


class CareerWorkflowAiResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    output: dict[str, object]
    provider_used: str
    requested_provider: str
    fallback_used: bool = False
    run_id: str


_OUTPUT_SCHEMAS: dict[CareerWorkflowTask, type[BaseModel]] = {
    "interview_question_generation": InterviewQuestionGenerationOutput,
    "interview_answer_drafting": InterviewAnswerDraftingOutput,
    "star_story_structuring": StarStoryStructuringOutput,
    "follow_up_drafting": FollowUpDraftingOutput,
    "career_plan_explanation": CareerPlanExplanationOutput,
    "certification_recommendation_explanation": CertificationRecommendationExplanationOutput,
    "project_gap_recommendation": ProjectGapRecommendationOutput,
    "opportunity_enrichment": OpportunityEnrichmentOutput,
    "taxonomy_mapping_explanation": TaxonomyMappingExplanationOutput,
}


def run_career_workflow_ai(
    task_id: CareerWorkflowTask,
    payload: dict[str, object],
    *,
    provider: Any | None = None,
    external_ai_opt_in: bool = False,
    source_refs: list[str] | None = None,
) -> CareerWorkflowAiResult:
    """Run one task through the standard registry; never bypass explicit external opt-in."""
    task = default_ai_task_registry().get(task_id)
    schema = _OUTPUT_SCHEMAS[task_id]
    requested = str(getattr(provider, "name", "local") or "local")
    started_at = datetime.now(UTC)
    started_monotonic = time.perf_counter()
    if provider is not None and requested != "local" and external_ai_opt_in:
        try:
            prompt = default_prompt_registry().get(task.prompt_id, task.prompt_version)
            output = schema.model_validate(provider.generate_structured(prompt, payload))
            trace = record_ai_run(
                task_id,
                provider_requested=requested,
                provider_used=requested,
                model_requested=str(getattr(provider, "model", requested)),
                model_used=str(getattr(provider, "model", requested)),
                provider=provider,
                started_at=started_at,
                started_monotonic=started_monotonic,
                evidence_count=len(source_refs or []),
                source_refs=source_refs,
                warnings=list(getattr(output, "warnings", [])),
            )
            return _result(task_id, output, requested, requested, trace.run_id)
        except Exception as exc:
            output = _local_fallback(
                task_id,
                warning=(
                    "Provider indisponivel; fallback local conservador usado. "
                    + sanitize_provider_message(exc, limit=160)
                ),
            )
            trace = record_ai_run(
                task_id,
                provider_requested=requested,
                provider_used="local",
                model_requested=str(getattr(provider, "model", requested)),
                model_used="local",
                fallback_used=True,
                fallback_reason="Provider indisponivel; fallback local conservador usado.",
                provider=provider,
                started_at=started_at,
                started_monotonic=started_monotonic,
                evidence_count=len(source_refs or []),
                source_refs=source_refs,
                warnings=list(getattr(output, "warnings", [])),
                error_type=type(exc).__name__,
            )
            return _result(task_id, output, "local", requested, trace.run_id, fallback=True)

    warning = (
        "Provider externo nao autorizado; fallback local usado."
        if provider is not None and requested != "local"
        else "Fallback local: nenhum fato novo foi criado."
    )
    output = _local_fallback(task_id, warning=warning)
    trace = record_ai_run(
        task_id,
        provider_requested=requested,
        provider_used="local",
        model_requested=str(getattr(provider, "model", "local")),
        model_used="local",
        fallback_used=provider is not None and requested != "local",
        fallback_reason=warning,
        started_at=started_at,
        started_monotonic=started_monotonic,
        evidence_count=len(source_refs or []),
        source_refs=source_refs,
        warnings=list(getattr(output, "warnings", [])),
    )
    return _result(
        task_id,
        output,
        "local",
        requested,
        trace.run_id,
        fallback=provider is not None and requested != "local",
    )


def _local_fallback(task_id: CareerWorkflowTask, *, warning: str) -> BaseModel:
    schema = _OUTPUT_SCHEMAS[task_id]
    return schema.model_validate({"warnings": [warning], "needs_user_review": True})


def _result(
    task_id: CareerWorkflowTask,
    output: BaseModel,
    provider_used: str,
    requested_provider: str,
    run_id: str,
    *,
    fallback: bool = False,
) -> CareerWorkflowAiResult:
    return CareerWorkflowAiResult(
        task_id=task_id,
        output=output.model_dump(mode="json"),
        provider_used=provider_used,
        requested_provider=requested_provider,
        fallback_used=fallback,
        run_id=run_id,
    )


__all__ = [
    "CareerWorkflowAiResult",
    "CareerWorkflowTask",
    "run_career_workflow_ai",
]
