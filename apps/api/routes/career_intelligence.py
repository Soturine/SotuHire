"""Domain matching policy inspection and deterministic scoring endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from modules.matching import DomainMatchingPolicy, policy_for_domain
from modules.matching.domain_weights import CareerDomain
from pydantic import BaseModel, ConfigDict, Field

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope

router = APIRouter(prefix="/api/v1/career-intelligence", tags=["career-intelligence"])

DOMAINS: tuple[CareerDomain, ...] = (
    "technology",
    "engineering",
    "healthcare",
    "education",
    "law",
    "research",
    "administration",
    "finance",
    "design",
    "tourism_services",
    "public_exams",
    "early_career",
    "career_transition",
)


class DomainScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: CareerDomain
    dimensions: dict[str, float] = Field(default_factory=dict, max_length=20)


class DomainScoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy: DomainMatchingPolicy
    score: float = Field(ge=0, le=100)
    ignored_dimensions: list[str] = Field(default_factory=list)


@router.get("/policies", response_model=ApiEnvelope[list[DomainMatchingPolicy]])
def domain_policies() -> ApiEnvelope[list[DomainMatchingPolicy]]:
    return ok([policy_for_domain(domain) for domain in DOMAINS])


@router.post("/score", response_model=ApiEnvelope[DomainScoreResponse])
def domain_score(payload: DomainScoreRequest) -> ApiEnvelope[DomainScoreResponse]:
    policy = policy_for_domain(payload.domain)
    ignored = sorted(set(payload.dimensions) - set(policy.applicable_dimensions))
    return ok(
        DomainScoreResponse(
            policy=policy,
            score=policy.score(payload.dimensions),
            ignored_dimensions=ignored,
        )
    )


__all__ = ["router"]
