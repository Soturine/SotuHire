"""Human-approval boundary and deterministic Copilot orchestration."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from modules.career_actions.models import CareerTask

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
from .tools import CreateTaskInput, ToolRegistry, default_tool_registry


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
        # Identity of the business intent the human approves: tool, exact payload, the
        # evidence offered as justification and the state it was derived from. ``reason`` is
        # explanatory text and deliberately not part of the identity.
        canonical = json.dumps(
            {
                "tool": tool_id,
                "payload": validated,
                "evidence_refs": sorted(set(evidence_refs or [])),
                "state": state.dependency_hash,
            },
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
        """Apply an approved proposal, re-checking every approval condition at the effect.

        Inside one ``BEGIN IMMEDIATE`` transaction: the proposal must still be approved, not
        expired, and its dependency hash must match the career state as it is *now*. The local
        effect, the execution record, the status transition and the audit event then commit
        together, so a crash cannot leave an effect without its lifecycle (or the reverse) and
        a concurrent second ``execute`` finds the proposal already executed.
        """
        rejection = ""
        updated: ProposedAction | None = None
        result: dict[str, Any] = {}
        with self.repository.write_transaction() as connection:
            proposal = self.repository._proposal_in(connection, proposal_id)
            if proposal is None:
                raise KeyError(proposal_id)
            if proposal.status != ProposalStatus.APPROVED:
                raise PermissionError("Execution requires an approved proposal")
            self.registry.validate_input(proposal.action_type, proposal.after_preview)
            # The write lock is held, so no other writer can change the state between this
            # check and the effect below (WAL readers see the same committed snapshot).
            current_hash = self.state_engine.build().dependency_hash
            closed: ProposedAction | None = None
            if proposal.expires_at and proposal.expires_at <= utc_now():
                closed = self.repository._set_proposal_status(
                    connection, proposal, ProposalStatus.EXPIRED
                )
                rejection = "Proposal expired before execution; propose it again"
            elif proposal.dependency_hash and proposal.dependency_hash != current_hash:
                closed = self.repository._set_proposal_status(
                    connection, proposal, ProposalStatus.STALE
                )
                rejection = "Proposal is stale: its career-state dependencies changed"
            if closed is not None:
                self.repository._insert_audit(
                    connection,
                    "system",
                    f"proposal_{closed.status}",
                    proposal=closed,
                    reason=rejection,
                )
            else:
                result = self._execute_local(connection, proposal)
                self.repository._insert_execution(
                    connection, proposal, status="executed", result=result, after_snapshot=result
                )
                updated = self.repository._set_proposal_status(
                    connection, proposal, ProposalStatus.EXECUTED, timestamp_field="executed_at"
                )
                self.repository._insert_audit(
                    connection, "human", "proposal_executed", proposal=updated
                )
        if rejection or updated is None:
            raise PermissionError(rejection or "Execution did not complete")
        return {"proposal": updated.model_dump(mode="json"), "result": result}

    def undo(self, proposal_id: str) -> ProposedAction:
        """Revert an executed proposal only if its effect is still exactly as it left it.

        The execution record holds the row version the effect produced. If the evidence or
        task was changed afterwards (by the user or another action) the undo is refused as a
        conflict instead of overwriting the newer decision (no lost update).
        """
        with self.repository.write_transaction() as connection:
            proposal = self.repository._proposal_in(connection, proposal_id)
            if proposal is None:
                raise KeyError(proposal_id)
            if proposal.status != ProposalStatus.EXECUTED or not proposal.reversible:
                raise PermissionError("Only executed reversible proposals can be undone")
            execution = self.repository.last_execution(connection, proposal_id)
            effect = execution["result"] if execution else {}
            if proposal.action_type == "create_task":
                self._undo_task(connection, proposal, effect)
            elif proposal.action_type == "archive_evidence":
                self._undo_archive(connection, proposal, effect)
            else:
                raise PermissionError("Undo strategy is not executable")
            self.repository._insert_execution(
                connection,
                proposal,
                status="undone",
                result={"undone": True},
                after_snapshot=proposal.before_snapshot,
            )
            updated = self.repository._set_proposal_status(
                connection, proposal, ProposalStatus.UNDONE
            )
            self.repository._insert_audit(connection, "human", "proposal_undone", proposal=updated)
        return updated

    def _undo_task(self, connection: Any, proposal: ProposedAction, effect: dict[str, Any]) -> None:
        if not effect.get("created"):
            raise ValueError("Undo conflict: the task was not created by this proposal")
        cursor = connection.execute(
            "DELETE FROM career_tasks WHERE task_id=? AND status='pending' AND updated_at=?",
            (self._task_id(proposal), effect.get("updated_at")),
        )
        if cursor.rowcount != 1:
            raise ValueError("Undo conflict: the task changed after execution")

    @staticmethod
    def _undo_archive(connection: Any, proposal: ProposedAction, effect: dict[str, Any]) -> None:
        old = ReviewStatus(proposal.before_snapshot.get("review_status", "candidate"))
        cursor = connection.execute(
            """UPDATE evidence_nodes SET review_status=?, updated_at=?
            WHERE node_id=? AND review_status=? AND updated_at=?""",
            (
                old,
                utc_now().isoformat(),
                proposal.after_preview["node_id"],
                effect.get("review_status"),
                effect.get("updated_at"),
            ),
        )
        if cursor.rowcount != 1:
            raise ValueError("Undo conflict: the evidence changed after execution")

    def plan(self, intent: str) -> CopilotPlan:
        """Record ``intent`` and list the current deterministic next-best actions as steps.

        The intent is stored for the human's reference; it is not interpreted. The same career
        state yields the same steps for any intent (SH-AUD-015): this is a review checklist,
        not semantic planning, and it never creates proposals.
        """
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

    def transition_plan(self, plan_id: str, action: str) -> CopilotPlan:
        transitions = {
            "pause": ({"active"}, "paused"),
            "resume": ({"paused"}, "active"),
            "cancel": ({"active", "paused"}, "cancelled"),
        }
        if action not in transitions:
            raise ValueError("Unsupported plan transition")
        expected, target = transitions[action]
        plan = self.repository.transition_plan(plan_id, expected=expected, target=target)
        self.repository.audit("human", f"plan_{target}", payload={"plan_id": plan_id})
        return plan

    def _execute_local(self, connection: Any, proposal: ProposedAction) -> dict[str, Any]:
        """Write the effect on the caller's transaction; never commits on its own."""
        if proposal.action_type == "create_task":
            # Same row shape as CareerWorkflowRepository.save_task, so /api/career/tasks
            # (which rebuilds CareerTask from ``payload``) can read Copilot-created tasks.
            payload = CreateTaskInput.model_validate(proposal.after_preview)
            task = CareerTask(
                task_id=self._task_id(proposal),
                task_type=payload.task_type,
                title=payload.title,
                priority=payload.priority,
                due_at=payload.due_at,
                related_refs=[f"proposal:{proposal.proposal_id}", *proposal.evidence_refs],
            )
            serialized = task.model_dump(mode="json")
            cursor = connection.execute(
                """INSERT INTO career_tasks
                (task_id,task_type,title,status,priority,due_at,payload,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(task_id) DO NOTHING""",
                (
                    task.task_id,
                    task.task_type,
                    task.title,
                    task.status,
                    task.priority,
                    task.due_at.isoformat() if task.due_at else None,
                    task.model_dump_json(),
                    serialized["created_at"],
                    serialized["updated_at"],
                ),
            )
            created = cursor.rowcount == 1
            return {
                "task_id": task.task_id,
                "created": created,
                "updated_at": serialized["updated_at"] if created else None,
            }
        if proposal.action_type == "archive_evidence":
            node_id = proposal.after_preview["node_id"]
            updated_at = utc_now().isoformat()
            cursor = connection.execute(
                "UPDATE evidence_nodes SET review_status=?, updated_at=? WHERE node_id=?",
                (ReviewStatus.STALE, updated_at, node_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(node_id)
            return {
                "node_id": node_id,
                "review_status": ReviewStatus.STALE.value,
                "updated_at": updated_at,
            }
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
