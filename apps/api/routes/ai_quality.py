"""AI quality, trace and human-feedback endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from modules.ai.feedback import AiFeedback

from apps.api.routes.responses import ok
from apps.api.schemas.ai_quality import (
    AiFeedbackCreate,
    AiFeedbackPage,
    AiQualityCollection,
    AiQualitySummary,
    AiRunsPage,
)
from apps.api.schemas.common import ApiEnvelope
from apps.api.services.ai_quality import (
    create_feedback,
    delete_feedback,
    list_feedback,
    quality_benchmarks,
    quality_prompts,
    quality_providers,
    quality_runs,
    quality_summary,
)

router = APIRouter(prefix="/api/v1/ai", tags=["ai-quality"])


@router.get("/quality/summary", response_model=ApiEnvelope[AiQualitySummary])
def summary() -> ApiEnvelope[AiQualitySummary]:
    return ok(quality_summary())


@router.get("/quality/runs", response_model=ApiEnvelope[AiRunsPage])
def runs(
    task_id: str = "", provider: str = "", limit: int = 50, offset: int = 0
) -> ApiEnvelope[AiRunsPage]:
    return ok(quality_runs(task_id=task_id, provider=provider, limit=limit, offset=offset))


@router.get("/quality/providers", response_model=ApiEnvelope[AiQualityCollection])
def providers() -> ApiEnvelope[AiQualityCollection]:
    return ok(quality_providers())


@router.get("/quality/prompts", response_model=ApiEnvelope[AiQualityCollection])
def prompts() -> ApiEnvelope[AiQualityCollection]:
    return ok(quality_prompts())


@router.get("/quality/benchmarks", response_model=ApiEnvelope[AiQualityCollection])
def benchmarks(limit: int = 50, offset: int = 0) -> ApiEnvelope[AiQualityCollection]:
    return ok(quality_benchmarks(limit=limit, offset=offset))


@router.post("/feedback", response_model=ApiEnvelope[AiFeedback])
def feedback_create(payload: AiFeedbackCreate) -> ApiEnvelope[AiFeedback]:
    try:
        feedback = create_feedback(payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="AI run not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ok(feedback, request_id=payload.request_id)


@router.get("/feedback", response_model=ApiEnvelope[AiFeedbackPage])
def feedback_list(
    run_id: str = "", task_id: str = "", limit: int = 50, offset: int = 0
) -> ApiEnvelope[AiFeedbackPage]:
    return ok(list_feedback(run_id=run_id, task_id=task_id, limit=limit, offset=offset))


@router.delete("/feedback/{feedback_id}", response_model=ApiEnvelope[dict[str, bool]])
def feedback_delete(feedback_id: str) -> ApiEnvelope[dict[str, bool]]:
    if not delete_feedback(feedback_id):
        raise HTTPException(status_code=404, detail="Feedback not found")
    return ok({"deleted": True})
