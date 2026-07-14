"""Explicit application outcome event and aggregate endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from modules.outcomes import OutcomeEvent, OutcomeStore, OutcomeSummary

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope

router = APIRouter(prefix="/api/v1/outcomes", tags=["outcomes"])


@router.get("/summary", response_model=ApiEnvelope[OutcomeSummary])
def summary() -> ApiEnvelope[OutcomeSummary]:
    return ok(OutcomeStore().summary())


@router.post("/events", response_model=ApiEnvelope[OutcomeEvent])
def create_event(payload: OutcomeEvent) -> ApiEnvelope[OutcomeEvent]:
    try:
        return ok(OutcomeStore().save(payload))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Application not found") from exc


@router.get("/applications/{application_id}", response_model=ApiEnvelope[list[OutcomeEvent]])
def application_events(application_id: str) -> ApiEnvelope[list[OutcomeEvent]]:
    return ok(OutcomeStore().for_application(application_id))
