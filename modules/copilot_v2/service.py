"""Human-approval boundary and deterministic Copilot orchestration."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from modules.storage.database import connect_database

from .career_state import CareerStateEngine
from .models import (
    CopilotContextReceipt,
    CopilotPlan,
    CopilotPlanStep,
    ProposalStatus,
    ProposedAction,
    ReviewStatus,
)
from .repository import CopilotRepository, utc_now
from .tools import ToolRegistry, default_tool_registry


class CareerCopilot:
    """Plans and proposes; it never writes domain data before explicit approval."""

    def __init__(
        self,
        database_path: str | Path | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.repository = CopilotRepository(database_path)
        self.state_engine = CareerStateEngine(database_path)
        self.registry = registry or default_tool_registry()

    def context_receipt(
        self, *, purpose: str, external_share: bool = False
    ) -> CopilotContextReceipt:
        nodes = self.repository.list_nodes(review_status="confirmed", limit=100)
        safe = [node for node in nodes if not node.sensitive]
        selected = safe if external_share else nodes
        text = " ".join(f"{node.title} {node.summary}" for node in selected)
        return CopilotContextReceipt(
            purpose=purpose,
            item_count=len(selected),
            token_estimate=max(0, len(text) // 4),
            external_share=external_share,
            omitted_sensitive_items=len(nodes) - len(safe) if external_share else 0,
        )

    def propose(
        self,
        tool_id: str,
        payload: dict[str, Any],
        *,
        reason: str,
        evidence_refs: list[str] | None = None,
        source: str = "copilot",
    ) -> ProposedAction:
        tool = self.registry.get(tool_id)
        if tool.read_only:
            raise ValueError("Read-only tools do not create proposals")
        validated = self.registry.validate_input(tool_id, payload).model_dump(mode="json")
        state = self.state_engine.build()
        canonical = json.dumps(
            {"tool": tool_id, "payload": validated, "state": state.dependency_hash},
            sort_keys=True,
            separators=(",", ":"),
        )
        proposal = ProposedAction(
            proposal_id=uuid4().hex,
            action_type=tool_id,
            title=self._proposal_title(tool_id, validated),
            description=tool.description,
            reason=reason,
            source=source,
            evidence_refs=evidence_refs or [],
            affected_entities=self._affected(tool_id, validated),
            before_snapshot=self._before(tool_id, validated),
            after_preview=validated,
            risk=tool.risk_level,
            reversible=tool_id in {"create_task", "archive_evidence"},
            undo_strategy=(
                "Remove the created local task"
                if tool_id == "create_task"
                else "Restore the prior evidence review status"
                if tool_id == "archive_evidence"
                else ""
            ),
            dependency_hash=state.dependency_hash,
            idempotency_key=hashlib.sha256(canonical.encode()).hexdigest(),
            created_at=utc_now(),
            expires_at=utc_now() + timedelta(days=7),
        )
        return self.repository.save_proposal(proposal)

    def approve(self, proposal_id: str) -> ProposedAction:
        state = self.state_engine.build()
        return self.repository.transition_proposal(
            proposal_id,
            expected={ProposalStatus.PROPOSED, ProposalStatus.REVIEWING},
            target=ProposalStatus.APPROVED,
            timestamp_field="approved_at",
            current_dependency_hash=state.dependency_hash,
        )

    def reject(self, proposal_id: str) -> ProposedAction:
        return self.repository.transition_proposal(
            proposal_id,
            expected={ProposalStatus.PROPOSED, ProposalStatus.REVIEWING, ProposalStatus.APPROVED},
            target=ProposalStatus.REJECTED,
            timestamp_field="rejected_at",
        )

    def execute(self, proposal_id: str) -> dict[str, Any]:
        proposal = self.repository.get_proposal(proposal_id)
        if proposal is None:
            raise KeyError(proposal_id)
        if proposal.status != ProposalStatus.APPROVED:
            raise PermissionError("Execution requires an approved proposal")
        self.registry.validate_input(proposal.action_type, proposal.after_preview)
        result = self._execute_local(proposal)
        self.repository.record_execution(
            proposal, status="executed", result=result, after_snapshot=result
        )
        updated = self.repository.transition_proposal(
            proposal_id,
            expected={ProposalStatus.APPROVED},
            target=ProposalStatus.EXECUTED,
            timestamp_field="executed_at",
        )
        return {"proposal": updated.model_dump(mode="json"), "result": result}

    def undo(self, proposal_id: str) -> ProposedAction:
        proposal = self.repository.get_proposal(proposal_id)
        if proposal is None:
            raise KeyError(proposal_id)
        if proposal.status != ProposalStatus.EXECUTED or not proposal.reversible:
            raise PermissionError("Only executed reversible proposals can be undone")
        if proposal.action_type == "create_task":
            task_id = self._task_id(proposal)
            with connect_database(self.repository.database_path) as connection:
                connection.execute("DELETE FROM career_tasks WHERE task_id=?", (task_id,))
        elif proposal.action_type == "archive_evidence":
            old = proposal.before_snapshot.get("review_status", "candidate")
            self.repository.review_node(proposal.after_preview["node_id"], ReviewStatus(old))
        else:
            raise PermissionError("Undo strategy is not executable")
        updated = self.repository.transition_proposal(
            proposal_id,
            expected={ProposalStatus.EXECUTED},
            target=ProposalStatus.UNDONE,
        )
        self.repository.audit("human", "proposal_undone", proposal=updated)
        return updated

    def plan(self, intent: str) -> CopilotPlan:
        if not intent.strip():
            raise ValueError("Intent is required")
        state = self.state_engine.build()
        now = utc_now()
        steps = [
            CopilotPlanStep(
                step_id=uuid4().hex,
                position=index,
                title=f"Revisar: {candidate.reason}",
                status="ready",
                payload={"action_type": candidate.type, "evidence_refs": candidate.evidence_refs},
            )
            for index, candidate in enumerate(state.recommendation_candidates[:5])
        ]
        plan = CopilotPlan(
            plan_id=uuid4().hex,
            intent=intent.strip(),
            title="Plano de carreira sob aprovação humana",
            status="active",
            context_summary={
                "dependency_hash": state.dependency_hash,
                "recommendations": len(steps),
                "ignored": "sensitive provider context and unconfirmed claims",
            },
            steps=steps,
            created_at=now,
            updated_at=now,
        )
        return self.repository.save_plan(plan)

    def _execute_local(self, proposal: ProposedAction) -> dict[str, Any]:
        if proposal.action_type == "create_task":
            task_id = self._task_id(proposal)
            payload = proposal.after_preview
            now = utc_now().isoformat()
            with connect_database(self.repository.database_path) as connection:
                connection.execute(
                    """INSERT INTO career_tasks
                    (task_id,task_type,title,status,priority,due_at,payload,created_at,updated_at)
                    VALUES (?,?,?,'pending',?,?,?, ?, ?)
                    ON CONFLICT(task_id) DO NOTHING""",
                    (
                        task_id,
                        payload["task_type"],
                        payload["title"],
                        payload["priority"],
                        payload.get("due_at"),
                        "{}",
                        now,
                        now,
                    ),
                )
            return {"task_id": task_id, "created": True}
        if proposal.action_type == "archive_evidence":
            node = self.repository.review_node(
                proposal.after_preview["node_id"], ReviewStatus.STALE
            )
            return {"node_id": node.node_id, "review_status": node.review_status}
        if proposal.action_type.startswith("draft_"):
            return {"draft": proposal.after_preview, "local_only": True}
        raise PermissionError(f"Tool has no safe local executor: {proposal.action_type}")

    def _before(self, tool_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if tool_id == "archive_evidence":
            node = self.repository.get_node(payload["node_id"])
            if node is None:
                raise KeyError(payload["node_id"])
            return {"node_id": node.node_id, "review_status": node.review_status}
        return {}

    @staticmethod
    def _affected(tool_id: str, payload: dict[str, Any]) -> list[str]:
        if tool_id == "archive_evidence":
            return [payload["node_id"]]
        return [tool_id]

    @staticmethod
    def _proposal_title(tool_id: str, payload: dict[str, Any]) -> str:
        return str(payload.get("title") or f"Proposta: {tool_id}")

    @staticmethod
    def _task_id(proposal: ProposedAction) -> str:
        return f"copilot-{proposal.proposal_id}"
