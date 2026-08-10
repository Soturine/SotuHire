"""Local career tasks, reminders, plans, and explicit calendar export."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import cast

from fastapi import APIRouter, HTTPException, Query
from modules.ai.career_workflows import (
    CareerWorkflowAiResult,
    CareerWorkflowTask,
    run_career_workflow_ai,
)
from modules.career_actions import (
    CareerPlan,
    CareerTask,
    Reminder,
    export_ics_event,
)
from modules.storage import CareerWorkflowRepository
from pydantic import BaseModel, ConfigDict, Field

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.services.ai_settings import get_ai_runtime

router = APIRouter(prefix="/api/v1/career", tags=["career-actions"])


class CalendarExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: str = Field(min_length=1, max_length=80)
    entity_id: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=300)
    starts_at: datetime
    ends_at: datetime | None = None
    description: str = Field(default="", max_length=10_000)
    location: str = Field(default="", max_length=500)


class CalendarExportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_name: str
    media_type: str = "text/calendar; charset=utf-8"
    content: str
    imported_automatically: bool = False


class CareerAiRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: dict[str, object] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list, max_length=100)
    external_ai_opt_in: bool = False


@router.get("/tasks", response_model=ApiEnvelope[list[CareerTask]])
def list_tasks(
    limit: int = Query(default=200, ge=1, le=1000),
) -> ApiEnvelope[list[CareerTask]]:
    return ok(CareerWorkflowRepository().list_tasks(limit=limit))


@router.post("/tasks", response_model=ApiEnvelope[CareerTask], status_code=201)
def save_task(payload: CareerTask) -> ApiEnvelope[CareerTask]:
    return ok(CareerWorkflowRepository().save_task(payload))


@router.get("/reminders", response_model=ApiEnvelope[list[Reminder]])
def list_reminders(
    limit: int = Query(default=200, ge=1, le=1000),
) -> ApiEnvelope[list[Reminder]]:
    return ok(CareerWorkflowRepository().list_reminders(limit=limit))


@router.post("/reminders", response_model=ApiEnvelope[Reminder], status_code=201)
def save_reminder(payload: Reminder) -> ApiEnvelope[Reminder]:
    try:
        return ok(CareerWorkflowRepository().save_reminder(payload))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Tarefa vinculada nao existe.") from exc


@router.get("/plans", response_model=ApiEnvelope[list[CareerPlan]])
def list_plans(
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiEnvelope[list[CareerPlan]]:
    return ok(CareerWorkflowRepository().list_career_plans(limit=limit))


@router.post("/plans", response_model=ApiEnvelope[CareerPlan], status_code=201)
def save_plan(payload: CareerPlan) -> ApiEnvelope[CareerPlan]:
    return ok(CareerWorkflowRepository().save_career_plan(payload))


@router.post("/calendar/export", response_model=ApiEnvelope[CalendarExportResponse])
def export_calendar(
    payload: CalendarExportRequest,
) -> ApiEnvelope[CalendarExportResponse]:
    try:
        content = export_ics_event(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return ok(
        CalendarExportResponse(
            file_name=f"sotuhire-{payload.entity_type}-{payload.entity_id}.ics",
            content=content,
        )
    )


@router.post(
    "/ai/{task_id}",
    response_model=ApiEnvelope[CareerWorkflowAiResult],
)
def career_ai(
    task_id: str,
    payload: CareerAiRequest,
) -> ApiEnvelope[CareerWorkflowAiResult]:
    allowed = {
        "career_plan_explanation",
        "certification_recommendation_explanation",
        "project_gap_recommendation",
        "opportunity_enrichment",
        "taxonomy_mapping_explanation",
    }
    if task_id not in allowed:
        raise HTTPException(status_code=404, detail="Task de carreira nao registrada.")
    runtime = get_ai_runtime("career_advice")
    result = run_career_workflow_ai(
        cast(CareerWorkflowTask, task_id),
        payload.payload,
        provider=runtime.provider if runtime.use_ai else None,
        external_ai_opt_in=payload.external_ai_opt_in,
        source_refs=payload.source_refs,
    )
    return ok(result)


__all__ = ["router"]
