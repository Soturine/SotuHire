"""Local interview, STAR, answer, and follow-up endpoints."""

from __future__ import annotations

import sqlite3
from typing import cast

from fastapi import APIRouter, HTTPException, Query
from modules.ai.career_workflows import (
    CareerWorkflowAiResult,
    CareerWorkflowTask,
    run_career_workflow_ai,
)
from modules.interviews import (
    FollowUpDraft,
    InterviewDraftAnswer,
    InterviewPreparation,
    InterviewQuestion,
    InterviewSession,
    StarStory,
    prepare_interview_local,
)
from modules.storage import CareerWorkflowRepository
from pydantic import BaseModel, ConfigDict, Field

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.services.ai_settings import get_ai_runtime

router = APIRouter(prefix="/api/v1/interviews", tags=["interviews"])


class ConfirmedInterviewEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    description: str = ""
    source_ref: str = ""
    confirmed_by_user: bool = False


class InterviewPrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_summary: str = Field(default="", max_length=20_000)
    requirements: list[str] = Field(default_factory=list, max_length=100)
    evidence: list[ConfirmedInterviewEvidence] = Field(default_factory=list, max_length=200)


class InterviewAiRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: dict[str, object] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list, max_length=100)
    external_ai_opt_in: bool = False


@router.get("", response_model=ApiEnvelope[list[InterviewSession]])
def list_interviews(
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiEnvelope[list[InterviewSession]]:
    return ok(CareerWorkflowRepository().list_interviews(limit=limit))


@router.post("", response_model=ApiEnvelope[InterviewSession], status_code=201)
def save_interview(payload: InterviewSession) -> ApiEnvelope[InterviewSession]:
    try:
        return ok(CareerWorkflowRepository().save_interview(payload))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Vinculo da entrevista nao existe.") from exc


@router.get(
    "/{session_id}/preparation",
    response_model=ApiEnvelope[InterviewPreparation],
)
def get_preparation(session_id: str) -> ApiEnvelope[InterviewPreparation]:
    value = CareerWorkflowRepository().get_preparation(session_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Preparacao de entrevista nao encontrada.")
    return ok(value)


@router.post(
    "/{session_id}/prepare",
    response_model=ApiEnvelope[InterviewPreparation],
)
def prepare_interview(
    session_id: str,
    payload: InterviewPrepareRequest,
) -> ApiEnvelope[InterviewPreparation]:
    repository = CareerWorkflowRepository()
    session = repository.get_interview(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Entrevista nao encontrada.")
    confirmed = [
        item.model_dump(mode="json") for item in payload.evidence if item.confirmed_by_user
    ]
    preparation = prepare_interview_local(
        session,
        opportunity_summary=payload.opportunity_summary,
        requirements=payload.requirements,
        confirmed_evidence=confirmed,
    )
    return ok(repository.save_preparation(preparation))


@router.get("/star-stories", response_model=ApiEnvelope[list[StarStory]])
def list_star_stories(
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiEnvelope[list[StarStory]]:
    return ok(CareerWorkflowRepository().list_star_stories(limit=limit))


@router.post("/star-stories", response_model=ApiEnvelope[StarStory], status_code=201)
def save_star_story(payload: StarStory) -> ApiEnvelope[StarStory]:
    return ok(CareerWorkflowRepository().save_star_story(payload))


@router.get("/questions", response_model=ApiEnvelope[list[InterviewQuestion]])
def list_questions(
    session_id: str = "",
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiEnvelope[list[InterviewQuestion]]:
    return ok(CareerWorkflowRepository().list_questions(session_id=session_id, limit=limit))


@router.post("/questions", response_model=ApiEnvelope[InterviewQuestion], status_code=201)
def save_question(payload: InterviewQuestion) -> ApiEnvelope[InterviewQuestion]:
    try:
        return ok(CareerWorkflowRepository().save_question(payload))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Entrevista vinculada nao existe.") from exc


@router.get("/answers", response_model=ApiEnvelope[list[InterviewDraftAnswer]])
def list_answers(
    question_id: str = "",
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiEnvelope[list[InterviewDraftAnswer]]:
    return ok(CareerWorkflowRepository().list_answers(question_id=question_id, limit=limit))


@router.post("/answers", response_model=ApiEnvelope[InterviewDraftAnswer], status_code=201)
def save_answer(payload: InterviewDraftAnswer) -> ApiEnvelope[InterviewDraftAnswer]:
    try:
        return ok(CareerWorkflowRepository().save_answer(payload))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Pergunta vinculada nao existe.") from exc


@router.get("/follow-ups", response_model=ApiEnvelope[list[FollowUpDraft]])
def list_follow_ups(
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiEnvelope[list[FollowUpDraft]]:
    return ok(CareerWorkflowRepository().list_follow_ups(limit=limit))


@router.post("/follow-ups", response_model=ApiEnvelope[FollowUpDraft], status_code=201)
def save_follow_up(payload: FollowUpDraft) -> ApiEnvelope[FollowUpDraft]:
    try:
        return ok(CareerWorkflowRepository().save_follow_up(payload))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Vinculo do follow-up nao existe.") from exc


@router.post(
    "/ai/{task_id}",
    response_model=ApiEnvelope[CareerWorkflowAiResult],
)
def interview_ai(
    task_id: str,
    payload: InterviewAiRequest,
) -> ApiEnvelope[CareerWorkflowAiResult]:
    allowed = {
        "interview_question_generation",
        "interview_answer_drafting",
        "star_story_structuring",
        "follow_up_drafting",
    }
    if task_id not in allowed:
        raise HTTPException(status_code=404, detail="Task de entrevista nao registrada.")
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
