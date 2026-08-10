"""SotuHire v2 Career Cockpit, evidence, portfolio and approval APIs."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from modules.copilot_v2 import CareerCopilot, CareerStateEngine, CopilotRepository
from modules.copilot_v2.models import (
    CopilotContextReceipt,
    CopilotPlan,
    EvidenceEdge,
    EvidenceNode,
    EvidenceNodeType,
    EvidenceRelationType,
    PortfolioItem,
    PortfolioType,
    ProposedAction,
    ReviewStatus,
)
from modules.copilot_v2.repository import utc_now
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope

router = APIRouter(prefix="/api/v2", tags=["career-copilot-v2"])


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceNodeCreate(StrictRequest):
    node_id: str = ""
    node_type: EvidenceNodeType
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(default="", max_length=10_000)
    payload: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list, max_length=100)
    confidence: float = Field(default=0, ge=0, le=1)
    sensitive: bool = False


class EvidenceReviewRequest(StrictRequest):
    review_status: ReviewStatus


class EvidenceEdgeCreate(StrictRequest):
    edge_id: str = ""
    source_id: str
    target_id: str
    relation_type: EvidenceRelationType
    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)


class PortfolioItemCreate(StrictRequest):
    portfolio_item_id: str = ""
    title: str = Field(min_length=1, max_length=240)
    type: PortfolioType
    description: str = Field(default="", max_length=20_000)
    role: str = Field(default="", max_length=240)
    links: list[HttpUrl] = Field(default_factory=list, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=100)
    tools: list[str] = Field(default_factory=list, max_length=100)
    evidence_refs: list[str] = Field(default_factory=list, max_length=100)
    source_refs: list[str] = Field(default_factory=list, max_length=100)
    visibility: str = "private"


class ProposalCreate(StrictRequest):
    tool_id: str
    input: dict[str, Any]
    reason: str = Field(min_length=1, max_length=2_000)
    evidence_refs: list[str] = Field(default_factory=list, max_length=100)


class CopilotPlanCreate(StrictRequest):
    intent: str = Field(min_length=1, max_length=4_000)


class GlobalSearchResult(StrictRequest):
    entity_type: str
    entity_id: str
    title: str
    subtitle: str = ""
    route: str
    review_status: str = ""


def _repository() -> CopilotRepository:
    return CopilotRepository()


def _copilot() -> CareerCopilot:
    return CareerCopilot()


@router.get("/career-state", response_model=ApiEnvelope[dict[str, Any]])
def career_state(persist: bool = False) -> ApiEnvelope[dict[str, Any]]:
    state = CareerStateEngine().build(persist=persist)
    return ok(state.model_dump(mode="json"))


@router.get("/evidence", response_model=ApiEnvelope[list[EvidenceNode]])
def list_evidence(
    review_status: ReviewStatus | None = None,
    node_type: EvidenceNodeType | None = None,
    query: str = Query(default="", max_length=200),
    limit: int = Query(default=200, ge=1, le=1_000),
) -> ApiEnvelope[list[EvidenceNode]]:
    return ok(
        _repository().list_nodes(
            review_status=review_status,
            node_type=node_type,
            query=query,
            limit=limit,
        )
    )


@router.post("/evidence", status_code=201, response_model=ApiEnvelope[EvidenceNode])
def create_evidence(payload: EvidenceNodeCreate) -> ApiEnvelope[EvidenceNode]:
    now = utc_now()
    node = EvidenceNode(
        node_id=payload.node_id or uuid4().hex,
        node_type=payload.node_type,
        title=payload.title,
        summary=payload.summary,
        payload=payload.payload,
        source_refs=payload.source_refs or ["manual:user"],
        confidence=payload.confidence,
        sensitive=payload.sensitive,
        created_at=now,
        updated_at=now,
    )
    return ok(_repository().save_node(node))


@router.patch("/evidence/{node_id}/review", response_model=ApiEnvelope[EvidenceNode])
def review_evidence(node_id: str, payload: EvidenceReviewRequest) -> ApiEnvelope[EvidenceNode]:
    try:
        return ok(_repository().review_node(node_id, payload.review_status))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Evidence not found") from exc


@router.get("/evidence/edges", response_model=ApiEnvelope[list[EvidenceEdge]])
def list_edges(
    node_id: str = Query(default="", max_length=128),
) -> ApiEnvelope[list[EvidenceEdge]]:
    return ok(_repository().list_edges(node_id=node_id))


@router.post("/evidence/edges", status_code=201, response_model=ApiEnvelope[EvidenceEdge])
def create_edge(payload: EvidenceEdgeCreate) -> ApiEnvelope[EvidenceEdge]:
    repository = _repository()
    if not repository.get_node(payload.source_id) or not repository.get_node(payload.target_id):
        raise HTTPException(status_code=404, detail="Evidence endpoint not found")
    now = utc_now()
    edge = EvidenceEdge(
        edge_id=payload.edge_id or uuid4().hex,
        source_id=payload.source_id,
        target_id=payload.target_id,
        relation_type=payload.relation_type,
        evidence_refs=payload.evidence_refs,
        source_refs=payload.source_refs,
        confidence=payload.confidence,
        created_at=now,
        updated_at=now,
    )
    return ok(repository.save_edge(edge))


@router.get("/portfolio", response_model=ApiEnvelope[list[PortfolioItem]])
def list_portfolio() -> ApiEnvelope[list[PortfolioItem]]:
    return ok(_repository().list_portfolio_items())


@router.post("/portfolio", status_code=201, response_model=ApiEnvelope[PortfolioItem])
def create_portfolio_item(payload: PortfolioItemCreate) -> ApiEnvelope[PortfolioItem]:
    now = utc_now()
    item = PortfolioItem(
        portfolio_item_id=payload.portfolio_item_id or uuid4().hex,
        title=payload.title,
        type=payload.type,
        description=payload.description,
        role=payload.role,
        links=payload.links,
        skills=payload.skills,
        tools=payload.tools,
        evidence_refs=payload.evidence_refs,
        source_refs=payload.source_refs or ["manual:user"],
        visibility=payload.visibility,
        created_at=now,
        updated_at=now,
    )
    return ok(_repository().save_portfolio_item(item))


@router.get("/approvals", response_model=ApiEnvelope[list[ProposedAction]])
def approval_queue(
    status: str = Query(default="", max_length=20),
) -> ApiEnvelope[list[ProposedAction]]:
    return ok(_repository().list_proposals(status=status))


@router.post("/approvals", status_code=201, response_model=ApiEnvelope[ProposedAction])
def create_proposal(payload: ProposalCreate) -> ApiEnvelope[ProposedAction]:
    try:
        return ok(
            _copilot().propose(
                payload.tool_id,
                payload.input,
                reason=payload.reason,
                evidence_refs=payload.evidence_refs,
            )
        )
    except (KeyError, ValueError, PermissionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/approvals/{proposal_id}/approve", response_model=ApiEnvelope[ProposedAction])
def approve_proposal(proposal_id: str) -> ApiEnvelope[ProposedAction]:
    return _proposal_transition(lambda: _copilot().approve(proposal_id))


@router.post("/approvals/{proposal_id}/reject", response_model=ApiEnvelope[ProposedAction])
def reject_proposal(proposal_id: str) -> ApiEnvelope[ProposedAction]:
    return _proposal_transition(lambda: _copilot().reject(proposal_id))


@router.post("/approvals/{proposal_id}/execute", response_model=ApiEnvelope[dict[str, Any]])
def execute_proposal(proposal_id: str) -> ApiEnvelope[dict[str, Any]]:
    return _proposal_transition(lambda: _copilot().execute(proposal_id))


@router.post("/approvals/{proposal_id}/undo", response_model=ApiEnvelope[ProposedAction])
def undo_proposal(proposal_id: str) -> ApiEnvelope[ProposedAction]:
    return _proposal_transition(lambda: _copilot().undo(proposal_id))


@router.post("/copilot/plans", status_code=201, response_model=ApiEnvelope[CopilotPlan])
def create_plan(payload: CopilotPlanCreate) -> ApiEnvelope[CopilotPlan]:
    return ok(_copilot().plan(payload.intent))


@router.post("/copilot/plans/{plan_id}/{action}", response_model=ApiEnvelope[CopilotPlan])
def transition_plan(plan_id: str, action: str) -> ApiEnvelope[CopilotPlan]:
    try:
        return ok(_copilot().transition_plan(plan_id, action))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plan not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/copilot/tools", response_model=ApiEnvelope[list[dict[str, Any]]])
def list_tools() -> ApiEnvelope[list[dict[str, Any]]]:
    tools = [
        {
            "tool_id": tool.tool_id,
            "description": tool.description,
            "input_schema": tool.input_schema.model_json_schema(),
            "output_schema": tool.output_schema,
            "read_only": tool.read_only,
            "requires_approval": tool.requires_approval,
            "risk_level": tool.risk_level,
            "domain": tool.domain,
            "category": tool.category,
        }
        for tool in _copilot().registry.list()
    ]
    return ok(tools)


@router.get("/copilot/context-preview", response_model=ApiEnvelope[CopilotContextReceipt])
def context_preview(
    purpose: str = Query(min_length=1, max_length=100), external_share: bool = False
) -> ApiEnvelope[CopilotContextReceipt]:
    return ok(_copilot().context_receipt(purpose=purpose, external_share=external_share))


@router.get("/audit", response_model=ApiEnvelope[list[dict[str, Any]]])
def audit_log(limit: int = Query(default=100, ge=1, le=1_000)) -> ApiEnvelope[list[dict[str, Any]]]:
    return ok(_repository().list_audit_events(limit=limit))


@router.get("/search", response_model=ApiEnvelope[list[GlobalSearchResult]])
def universal_search(
    query: str = Query(min_length=2, max_length=200),
) -> ApiEnvelope[list[GlobalSearchResult]]:
    repository = _repository()
    evidence = repository.list_nodes(query=query, limit=30)
    portfolio = [
        item
        for item in repository.list_portfolio_items(limit=100)
        if query.casefold() in f"{item.title} {item.description}".casefold()
    ][:20]
    results = [
        GlobalSearchResult(
            entity_type="evidence",
            entity_id=node.node_id,
            title=node.title,
            subtitle=node.node_type,
            route="/evidence",
            review_status=node.review_status,
        )
        for node in evidence
    ]
    results.extend(
        GlobalSearchResult(
            entity_type="portfolio",
            entity_id=item.portfolio_item_id,
            title=item.title,
            subtitle=item.type,
            route="/portfolio",
            review_status=item.review_status,
        )
        for item in portfolio
    )
    return ok(results)


def _proposal_transition(operation: Any) -> Any:
    try:
        return ok(operation())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Proposal not found") from exc
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


__all__ = ["router"]
