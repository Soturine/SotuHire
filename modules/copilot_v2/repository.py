"""SQLite-only repository for v2 structured career intelligence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from pydantic_core import to_jsonable_python

from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database

from .models import (
    CopilotPlan,
    EvidenceEdge,
    EvidenceNode,
    PortfolioItem,
    ProposalStatus,
    ProposedAction,
    ReviewStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def _json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        to_jsonable_python(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _loads(value: str) -> Any:
    return json.loads(value)


class CopilotRepository:
    """Single writer for evidence, portfolio, proposals, plans and audit events."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = Path(database_path) if database_path else default_database_path()

    def _ensure(self) -> None:
        ensure_database(self.database_path)

    def save_node(self, node: EvidenceNode) -> EvidenceNode:
        self._ensure()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO evidence_nodes
                (node_id,node_type,title,summary,payload,source_refs,review_status,confidence,
                 sensitive,created_at,updated_at,stale_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(node_id) DO UPDATE SET title=excluded.title, summary=excluded.summary,
                payload=excluded.payload, source_refs=excluded.source_refs,
                review_status=excluded.review_status, confidence=excluded.confidence,
                sensitive=excluded.sensitive, updated_at=excluded.updated_at,
                stale_at=excluded.stale_at""",
                (
                    node.node_id,
                    node.node_type,
                    node.title,
                    node.summary,
                    _json(node.payload),
                    _json(node.source_refs),
                    node.review_status,
                    node.confidence,
                    int(node.sensitive),
                    node.created_at.isoformat(),
                    node.updated_at.isoformat(),
                    node.stale_at.isoformat() if node.stale_at else None,
                ),
            )
        return node

    def get_node(self, node_id: str) -> EvidenceNode | None:
        self._ensure()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM evidence_nodes WHERE node_id=?", (node_id,)
            ).fetchone()
        return self._node(row) if row else None

    def list_nodes(
        self,
        *,
        review_status: ReviewStatus | str | None = None,
        node_type: str | None = None,
        query: str = "",
        limit: int = 200,
    ) -> list[EvidenceNode]:
        self._ensure()
        clauses: list[str] = []
        values: list[object] = []
        if review_status:
            clauses.append("review_status=?")
            values.append(str(review_status))
        if node_type:
            clauses.append("node_type=?")
            values.append(node_type)
        if query.strip():
            clauses.append("(title LIKE ? ESCAPE '\\' OR summary LIKE ? ESCAPE '\\')")
            escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            values.extend([f"%{escaped}%", f"%{escaped}%"])
        sql = "SELECT * FROM evidence_nodes"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        values.append(max(1, min(limit, 1_000)))
        with connect_database(self.database_path) as connection:
            rows = connection.execute(sql, values).fetchall()
        return [self._node(row) for row in rows]

    def review_node(self, node_id: str, status: ReviewStatus) -> EvidenceNode:
        node = self.get_node(node_id)
        if node is None:
            raise KeyError(node_id)
        updated = node.model_copy(update={"review_status": status, "updated_at": utc_now()})
        return self.save_node(updated)

    def save_edge(self, edge: EvidenceEdge) -> EvidenceEdge:
        self._ensure()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO evidence_edges
                (edge_id,source_id,target_id,relation_type,evidence_refs,source_refs,
                 review_status,confidence,created_at,updated_at,stale_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(source_id,target_id,relation_type) DO UPDATE SET
                evidence_refs=excluded.evidence_refs, source_refs=excluded.source_refs,
                review_status=excluded.review_status, confidence=excluded.confidence,
                updated_at=excluded.updated_at, stale_at=excluded.stale_at""",
                (
                    edge.edge_id,
                    edge.source_id,
                    edge.target_id,
                    edge.relation_type,
                    _json(edge.evidence_refs),
                    _json(edge.source_refs),
                    edge.review_status,
                    edge.confidence,
                    edge.created_at.isoformat(),
                    edge.updated_at.isoformat(),
                    edge.stale_at.isoformat() if edge.stale_at else None,
                ),
            )
        return edge

    def list_edges(self, *, node_id: str = "", limit: int = 500) -> list[EvidenceEdge]:
        self._ensure()
        sql = "SELECT * FROM evidence_edges"
        values: list[object] = []
        if node_id:
            sql += " WHERE source_id=? OR target_id=?"
            values.extend([node_id, node_id])
        sql += " ORDER BY updated_at DESC LIMIT ?"
        values.append(max(1, min(limit, 2_000)))
        with connect_database(self.database_path) as connection:
            rows = connection.execute(sql, values).fetchall()
        return [self._edge(row) for row in rows]

    def save_portfolio_item(self, item: PortfolioItem) -> PortfolioItem:
        self._ensure()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO portfolio_items
                (portfolio_item_id,title,item_type,description,role,start_date,end_date,links,
                 attachments,skills,tools,evidence_refs,source_refs,review_status,visibility,
                 created_at,updated_at,stale_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(portfolio_item_id) DO UPDATE SET title=excluded.title,
                item_type=excluded.item_type,description=excluded.description,role=excluded.role,
                start_date=excluded.start_date,end_date=excluded.end_date,links=excluded.links,
                attachments=excluded.attachments,skills=excluded.skills,tools=excluded.tools,
                evidence_refs=excluded.evidence_refs,source_refs=excluded.source_refs,
                review_status=excluded.review_status,visibility=excluded.visibility,
                updated_at=excluded.updated_at,stale_at=excluded.stale_at""",
                (
                    item.portfolio_item_id,
                    item.title,
                    item.type,
                    item.description,
                    item.role,
                    item.start_date,
                    item.end_date,
                    _json(item.links),
                    _json(item.attachments),
                    _json(item.skills),
                    _json(item.tools),
                    _json(item.evidence_refs),
                    _json(item.source_refs),
                    item.review_status,
                    item.visibility,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                    item.stale_at.isoformat() if item.stale_at else None,
                ),
            )
        return item

    def list_portfolio_items(self, *, limit: int = 200) -> list[PortfolioItem]:
        self._ensure()
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM portfolio_items ORDER BY updated_at DESC LIMIT ?",
                (max(1, min(limit, 1_000)),),
            ).fetchall()
        return [self._portfolio(row) for row in rows]

    def save_proposal(self, proposal: ProposedAction) -> ProposedAction:
        self._ensure()
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT * FROM proposed_actions WHERE idempotency_key=?",
                (proposal.idempotency_key,),
            ).fetchone()
            if existing:
                return self._proposal(existing)
            connection.execute(
                """INSERT INTO proposed_actions
                (proposal_id,action_type,title,description,reason,source,evidence_refs,
                 affected_entities,before_snapshot,after_preview,risk,reversible,undo_strategy,
                 status,dependency_hash,idempotency_key,created_at,approved_at,executed_at,
                 rejected_at,expires_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    proposal.proposal_id,
                    proposal.action_type,
                    proposal.title,
                    proposal.description,
                    proposal.reason,
                    proposal.source,
                    _json(proposal.evidence_refs),
                    _json(proposal.affected_entities),
                    _json(proposal.before_snapshot),
                    _json(proposal.after_preview),
                    proposal.risk,
                    int(proposal.reversible),
                    proposal.undo_strategy,
                    proposal.status,
                    proposal.dependency_hash,
                    proposal.idempotency_key,
                    proposal.created_at.isoformat(),
                    proposal.approved_at.isoformat() if proposal.approved_at else None,
                    proposal.executed_at.isoformat() if proposal.executed_at else None,
                    proposal.rejected_at.isoformat() if proposal.rejected_at else None,
                    proposal.expires_at.isoformat() if proposal.expires_at else None,
                ),
            )
        self.audit("system", "proposal_created", proposal=proposal, reason=proposal.reason)
        return proposal

    def get_proposal(self, proposal_id: str) -> ProposedAction | None:
        self._ensure()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM proposed_actions WHERE proposal_id=?", (proposal_id,)
            ).fetchone()
        return self._proposal(row) if row else None

    def list_proposals(self, *, status: str = "", limit: int = 200) -> list[ProposedAction]:
        self._ensure()
        sql = "SELECT * FROM proposed_actions"
        values: list[object] = []
        if status:
            sql += " WHERE status=?"
            values.append(status)
        sql += " ORDER BY created_at DESC LIMIT ?"
        values.append(max(1, min(limit, 1_000)))
        with connect_database(self.database_path) as connection:
            rows = connection.execute(sql, values).fetchall()
        return [self._proposal(row) for row in rows]

    def transition_proposal(
        self,
        proposal_id: str,
        *,
        expected: set[ProposalStatus],
        target: ProposalStatus,
        timestamp_field: str = "",
        current_dependency_hash: str | None = None,
    ) -> ProposedAction:
        proposal = self.get_proposal(proposal_id)
        if proposal is None:
            raise KeyError(proposal_id)
        if ProposalStatus(proposal.status) not in expected:
            raise ValueError(f"Invalid proposal transition: {proposal.status} -> {target}")
        now = utc_now()
        if proposal.expires_at and proposal.expires_at <= now:
            target = ProposalStatus.EXPIRED
        elif (
            current_dependency_hash is not None
            and proposal.dependency_hash
            and proposal.dependency_hash != current_dependency_hash
        ):
            target = ProposalStatus.STALE
        with connect_database(self.database_path) as connection:
            assignments = ["status=?"]
            values: list[object] = [target]
            if timestamp_field:
                assignments.append(f"{timestamp_field}=?")
                values.append(now.isoformat())
            values.extend([proposal_id, proposal.status])
            cursor = connection.execute(
                f"UPDATE proposed_actions SET {', '.join(assignments)} "
                "WHERE proposal_id=? AND status=?",
                values,
            )
            if cursor.rowcount != 1:
                raise ValueError("Concurrent proposal transition rejected")
        updated = self.get_proposal(proposal_id)
        assert updated is not None
        self.audit("human", f"proposal_{target}", proposal=updated)
        return updated

    def record_execution(
        self,
        proposal: ProposedAction,
        *,
        status: str,
        result: dict[str, Any],
        after_snapshot: dict[str, Any],
    ) -> str:
        execution_id = uuid4().hex
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO action_executions
                (execution_id,proposal_id,status,result,before_snapshot,after_snapshot,executed_at)
                VALUES (?,?,?,?,?,?,?)""",
                (
                    execution_id,
                    proposal.proposal_id,
                    status,
                    _json(result),
                    _json(proposal.before_snapshot),
                    _json(after_snapshot),
                    utc_now().isoformat(),
                ),
            )
        return execution_id

    def audit(
        self,
        actor: str,
        event_type: str,
        *,
        proposal: ProposedAction | None = None,
        reason: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._ensure()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO copilot_audit_events
                (event_id,actor,event_type,proposal_id,evidence_refs,reason,before_snapshot,
                 after_snapshot,payload,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    uuid4().hex,
                    actor,
                    event_type,
                    proposal.proposal_id if proposal else None,
                    _json(proposal.evidence_refs if proposal else []),
                    reason,
                    _json(proposal.before_snapshot if proposal else {}),
                    _json(proposal.after_preview if proposal else {}),
                    _json(payload or {}),
                    utc_now().isoformat(),
                ),
            )

    def save_career_state(
        self, profile_id: str, dependency_hash: str, payload: dict[str, Any], trigger: str
    ) -> str:
        snapshot_id = uuid4().hex
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO career_state_snapshots
                (snapshot_id,profile_id,dependency_hash,payload,trigger,created_at)
                VALUES (?,?,?,?,?,?)""",
                (
                    snapshot_id,
                    profile_id,
                    dependency_hash,
                    _json(payload),
                    trigger,
                    utc_now().isoformat(),
                ),
            )
        return snapshot_id

    def save_plan(self, plan: CopilotPlan) -> CopilotPlan:
        self._ensure()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO copilot_plans
                (plan_id,intent,title,status,context_summary,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(plan_id) DO UPDATE SET status=excluded.status,
                context_summary=excluded.context_summary,updated_at=excluded.updated_at""",
                (
                    plan.plan_id,
                    plan.intent,
                    plan.title,
                    plan.status,
                    _json(plan.context_summary),
                    plan.created_at.isoformat(),
                    plan.updated_at.isoformat(),
                ),
            )
            for step in plan.steps:
                connection.execute(
                    """INSERT INTO copilot_plan_steps
                    (step_id,plan_id,position,title,status,proposal_id,payload,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(step_id) DO UPDATE SET status=excluded.status,
                    proposal_id=excluded.proposal_id,payload=excluded.payload,
                    updated_at=excluded.updated_at""",
                    (
                        step.step_id,
                        plan.plan_id,
                        step.position,
                        step.title,
                        step.status,
                        step.proposal_id,
                        _json(step.payload),
                        plan.created_at.isoformat(),
                        plan.updated_at.isoformat(),
                    ),
                )
        return plan

    def list_audit_events(self, *, limit: int = 200) -> list[dict[str, Any]]:
        self._ensure()
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM copilot_audit_events ORDER BY created_at DESC LIMIT ?",
                (max(1, min(limit, 1_000)),),
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _node(row: Any) -> EvidenceNode:
        return EvidenceNode(
            node_id=row["node_id"],
            node_type=row["node_type"],
            title=row["title"],
            summary=row["summary"],
            payload=_loads(row["payload"]),
            source_refs=_loads(row["source_refs"]),
            review_status=row["review_status"],
            confidence=row["confidence"],
            sensitive=bool(row["sensitive"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            stale_at=row["stale_at"],
        )

    @staticmethod
    def _edge(row: Any) -> EvidenceEdge:
        return EvidenceEdge(
            edge_id=row["edge_id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation_type=row["relation_type"],
            evidence_refs=_loads(row["evidence_refs"]),
            source_refs=_loads(row["source_refs"]),
            review_status=row["review_status"],
            confidence=row["confidence"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            stale_at=row["stale_at"],
        )

    @staticmethod
    def _portfolio(row: Any) -> PortfolioItem:
        return PortfolioItem(
            portfolio_item_id=row["portfolio_item_id"],
            title=row["title"],
            type=row["item_type"],
            description=row["description"],
            role=row["role"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            links=_loads(row["links"]),
            attachments=_loads(row["attachments"]),
            skills=_loads(row["skills"]),
            tools=_loads(row["tools"]),
            evidence_refs=_loads(row["evidence_refs"]),
            source_refs=_loads(row["source_refs"]),
            review_status=row["review_status"],
            visibility=row["visibility"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            stale_at=row["stale_at"],
        )

    @staticmethod
    def _proposal(row: Any) -> ProposedAction:
        return ProposedAction(
            proposal_id=row["proposal_id"],
            action_type=row["action_type"],
            title=row["title"],
            description=row["description"],
            reason=row["reason"],
            source=row["source"],
            evidence_refs=_loads(row["evidence_refs"]),
            affected_entities=_loads(row["affected_entities"]),
            before_snapshot=_loads(row["before_snapshot"]),
            after_preview=_loads(row["after_preview"]),
            risk=row["risk"],
            reversible=bool(row["reversible"]),
            undo_strategy=row["undo_strategy"],
            status=row["status"],
            dependency_hash=row["dependency_hash"],
            idempotency_key=row["idempotency_key"],
            created_at=row["created_at"],
            approved_at=row["approved_at"],
            executed_at=row["executed_at"],
            rejected_at=row["rejected_at"],
            expires_at=row["expires_at"],
        )
