"""Public opportunity observations and explainable local ranking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query
from modules.opportunities import OpportunityCandidate, OpportunityPreferences, rank_opportunities
from modules.storage.career_intelligence import (
    CareerIntelligenceRepository,
    OpportunityObservationRecord,
    OpportunityRankingRecord,
)
from pydantic import BaseModel, ConfigDict, Field

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunity-intelligence"])


class OpportunityRankingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[OpportunityCandidate] = Field(min_length=1, max_length=500)
    preferences: OpportunityPreferences = Field(default_factory=OpportunityPreferences)
    profile_id: str = Field(default="", max_length=160)
    top_k: int = Field(default=20, ge=1, le=100)


@router.post(
    "/observations",
    response_model=ApiEnvelope[list[OpportunityObservationRecord]],
    status_code=201,
)
def save_observation(
    payload: OpportunityCandidate,
) -> ApiEnvelope[list[OpportunityObservationRecord]]:
    return ok(CareerIntelligenceRepository().save_candidate(payload))


@router.get("/candidates", response_model=ApiEnvelope[list[OpportunityCandidate]])
def list_candidates(
    limit: int = Query(default=200, ge=1, le=1_000),
) -> ApiEnvelope[list[OpportunityCandidate]]:
    return ok(CareerIntelligenceRepository().list_candidates(limit=limit))


@router.post(
    "/rankings",
    response_model=ApiEnvelope[list[OpportunityRankingRecord]],
    status_code=201,
)
def create_rankings(
    payload: OpportunityRankingRequest,
) -> ApiEnvelope[list[OpportunityRankingRecord]]:
    repository = CareerIntelligenceRepository()
    for candidate in payload.candidates:
        repository.save_candidate(candidate)
    ranked = rank_opportunities(
        payload.candidates,
        payload.preferences,
        top_k=payload.top_k,
    )
    return ok(repository.save_rankings(ranked, profile_id=payload.profile_id))


@router.get("/rankings", response_model=ApiEnvelope[list[OpportunityRankingRecord]])
def list_rankings(
    profile_id: str = Query(default="", max_length=160),
    limit: int = Query(default=200, ge=1, le=1_000),
) -> ApiEnvelope[list[OpportunityRankingRecord]]:
    return ok(CareerIntelligenceRepository().list_rankings(profile_id=profile_id, limit=limit))


__all__ = ["router"]
