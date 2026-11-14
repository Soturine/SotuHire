"""Integrity of the Copilot approval boundary at the point of effect.

Each test reproduces a defect found by the 2026-11 assurance audit (see
docs/assurance/FINDINGS.md). They exercise the real SQLite boundary, not mocks.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from modules.copilot_v2 import CareerCopilot, CareerStateEngine, CopilotRepository
from modules.copilot_v2.models import (
    EvidenceEdge,
    EvidenceNode,
    EvidenceNodeType,
    EvidenceRelationType,
    ProposalStatus,
    ReviewStatus,
)
from modules.storage.career_workflows import CareerWorkflowRepository
from modules.storage.database import connect_database


def _now() -> datetime:
    return datetime.now(UTC)


def _node(node_id: str, status: ReviewStatus = ReviewStatus.CONFIRMED) -> EvidenceNode:
    return EvidenceNode(
        node_id=node_id,
        node_type=EvidenceNodeType.PROJECT,
        title=f"Projeto sintético {node_id}",
        review_status=status,
        confidence=1,
        source_refs=["manual:test"],
        created_at=_now(),
        updated_at=_now(),
    )


def _task_proposal(copilot: CareerCopilot, title: str = "Revisar currículo"):
    return copilot.propose(
        "create_task",
        {"title": title, "task_type": "document", "priority": "high"},
        reason="Teste de integridade.",
    )


def _count(database: Path, sql: str, params: tuple[object, ...] = ()) -> int:
    with connect_database(database) as connection:
        return int(connection.execute(sql, params).fetchone()[0])


# SH-AUD-001 / SH-AUD-007 -------------------------------------------------------


def test_execute_revalidates_dependency_hash_after_approval(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    copilot = CareerCopilot(database)
    proposal = _task_proposal(copilot)
    approved = copilot.approve(proposal.proposal_id)
    assert approved.status == ProposalStatus.APPROVED

    # A relevant dependency changes between approval and execution.
    copilot.repository.save_node(_node("changed-after-approval"))

    with pytest.raises(PermissionError, match="stale"):
        copilot.execute(proposal.proposal_id)

    assert _count(database, "SELECT COUNT(*) FROM career_tasks") == 0
    assert _count(database, "SELECT COUNT(*) FROM action_executions") == 0
    persisted = copilot.repository.get_proposal(proposal.proposal_id)
    assert persisted is not None and persisted.status == ProposalStatus.STALE
    events = [event["event_type"] for event in copilot.repository.list_audit_events()]
    assert "proposal_stale" in events


def test_execute_rejects_expired_approved_proposal(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    copilot = CareerCopilot(database)
    proposal = _task_proposal(copilot)
    copilot.approve(proposal.proposal_id)
    with connect_database(database) as connection:
        connection.execute(
            "UPDATE proposed_actions SET expires_at=? WHERE proposal_id=?",
            ((_now() - timedelta(minutes=1)).isoformat(), proposal.proposal_id),
        )

    with pytest.raises(PermissionError, match="expired"):
        copilot.execute(proposal.proposal_id)

    assert _count(database, "SELECT COUNT(*) FROM career_tasks") == 0
    persisted = copilot.repository.get_proposal(proposal.proposal_id)
    assert persisted is not None and persisted.status == ProposalStatus.EXPIRED


# SH-AUD-002 --------------------------------------------------------------------


def test_effect_and_lifecycle_are_atomic_when_recording_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "sotuhire.db"
    copilot = CareerCopilot(database)
    proposal = _task_proposal(copilot)
    copilot.approve(proposal.proposal_id)

    def crash(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("simulated crash between effect and lifecycle")

    monkeypatch.setattr(copilot.repository, "_insert_execution", crash)

    with pytest.raises(RuntimeError, match="simulated crash"):
        copilot.execute(proposal.proposal_id)

    # No orphan effect: the task insert rolled back with the failed lifecycle write.
    assert _count(database, "SELECT COUNT(*) FROM career_tasks") == 0
    persisted = copilot.repository.get_proposal(proposal.proposal_id)
    assert persisted is not None and persisted.status == ProposalStatus.APPROVED

    monkeypatch.undo()
    result = copilot.execute(proposal.proposal_id)
    assert result["proposal"]["status"] == ProposalStatus.EXECUTED
    assert _count(database, "SELECT COUNT(*) FROM career_tasks") == 1


def test_concurrent_execute_applies_effect_once(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    seed = CareerCopilot(database)
    proposal = _task_proposal(seed)
    seed.approve(proposal.proposal_id)

    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def worker() -> None:
        copilot = CareerCopilot(database)
        barrier.wait()
        try:
            copilot.execute(proposal.proposal_id)
            outcomes.append("executed")
        except (PermissionError, ValueError):
            outcomes.append("rejected")

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(outcomes) == ["executed", "rejected"]
    assert _count(database, "SELECT COUNT(*) FROM action_executions") == 1
    assert _count(database, "SELECT COUNT(*) FROM career_tasks") == 1


# SH-AUD-003 --------------------------------------------------------------------


def test_undo_archive_does_not_overwrite_later_edit(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    copilot = CareerCopilot(database)
    copilot.repository.save_node(_node("evidence-1"))
    proposal = copilot.propose(
        "archive_evidence", {"node_id": "evidence-1"}, reason="Evidência obsoleta."
    )
    copilot.approve(proposal.proposal_id)
    copilot.execute(proposal.proposal_id)

    # A later, legitimate human decision on the same evidence.
    copilot.repository.review_node("evidence-1", ReviewStatus.REJECTED)

    with pytest.raises(ValueError, match="conflict"):
        copilot.undo(proposal.proposal_id)

    node = copilot.repository.get_node("evidence-1")
    assert node is not None and node.review_status == ReviewStatus.REJECTED
    persisted = copilot.repository.get_proposal(proposal.proposal_id)
    assert persisted is not None and persisted.status == ProposalStatus.EXECUTED


def test_undo_archive_restores_when_untouched(tmp_path: Path) -> None:
    copilot = CareerCopilot(tmp_path / "sotuhire.db")
    copilot.repository.save_node(_node("evidence-2"))
    proposal = copilot.propose(
        "archive_evidence", {"node_id": "evidence-2"}, reason="Evidência obsoleta."
    )
    copilot.approve(proposal.proposal_id)
    copilot.execute(proposal.proposal_id)

    undone = copilot.undo(proposal.proposal_id)

    node = copilot.repository.get_node("evidence-2")
    assert undone.status == ProposalStatus.UNDONE
    assert node is not None and node.review_status == ReviewStatus.CONFIRMED


def test_undo_task_does_not_delete_task_edited_by_user(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    copilot = CareerCopilot(database)
    proposal = _task_proposal(copilot)
    copilot.approve(proposal.proposal_id)
    result = copilot.execute(proposal.proposal_id)
    task_id = result["result"]["task_id"]

    workflows = CareerWorkflowRepository(database)
    task = next(item for item in workflows.list_tasks() if item.task_id == task_id)
    workflows.save_task(task.model_copy(update={"status": "completed", "updated_at": _now()}))

    with pytest.raises(ValueError, match="conflict"):
        copilot.undo(proposal.proposal_id)
    assert _count(database, "SELECT COUNT(*) FROM career_tasks") == 1


# SH-NEW-002: Copilot tasks must be readable by the Career workflows -------------


def test_copilot_created_task_is_listed_by_career_workflows(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    copilot = CareerCopilot(database)
    proposal = copilot.propose(
        "create_task",
        {
            "title": "Preparar entrevista",
            "task_type": "interview",
            "due_at": "2026-12-01T12:00:00-03:00",
        },
        reason="Entrevista registrada.",
    )
    copilot.approve(proposal.proposal_id)
    copilot.execute(proposal.proposal_id)

    tasks = CareerWorkflowRepository(database).list_tasks()

    assert [task.title for task in tasks] == ["Preparar entrevista"]
    assert tasks[0].due_at == datetime(2026, 12, 1, 15, 0, tzinfo=UTC)


# SH-AUD-005 --------------------------------------------------------------------


def test_save_edge_returns_persisted_identity(tmp_path: Path) -> None:
    repository = CopilotRepository(tmp_path / "sotuhire.db")
    repository.save_node(_node("project-a"))
    repository.save_node(_node("project-b"))

    def edge(edge_id: str, confidence: float) -> EvidenceEdge:
        return EvidenceEdge(
            edge_id=edge_id,
            source_id="project-a",
            target_id="project-b",
            relation_type=EvidenceRelationType.PROJECT_DEMONSTRATES_SKILL,
            confidence=confidence,
            created_at=_now(),
            updated_at=_now(),
        )

    first = repository.save_edge(edge("edge-original", 0.4))
    second = repository.save_edge(edge("edge-different-id", 0.9))

    persisted = repository.list_edges(node_id="project-a")
    assert len(persisted) == 1
    assert first.edge_id == second.edge_id == persisted[0].edge_id == "edge-original"
    assert second.confidence == persisted[0].confidence == 0.9


# SH-AUD-008 --------------------------------------------------------------------


def test_create_task_reports_honest_creation_flag(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    copilot = CareerCopilot(database)
    proposal = _task_proposal(copilot)
    copilot.approve(proposal.proposal_id)
    # Simulate a task already present under the deterministic id (e.g. restored backup).
    with connect_database(database) as connection:
        now = _now().isoformat()
        connection.execute(
            """INSERT INTO career_tasks
            (task_id,task_type,title,status,priority,due_at,payload,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                f"copilot-{proposal.proposal_id}",
                "document",
                "Revisar currículo",
                "pending",
                "high",
                None,
                "{}",
                now,
                now,
            ),
        )

    result = copilot.execute(proposal.proposal_id)

    assert result["result"]["created"] is False
    assert _count(database, "SELECT COUNT(*) FROM career_tasks") == 1


# SH-AUD-009 --------------------------------------------------------------------


def test_reproposal_after_rejection_creates_new_reviewable_proposal(tmp_path: Path) -> None:
    copilot = CareerCopilot(tmp_path / "sotuhire.db")
    first = _task_proposal(copilot)
    retry = _task_proposal(copilot)
    assert retry.proposal_id == first.proposal_id  # idempotent retry while still open

    copilot.reject(first.proposal_id)
    again = _task_proposal(copilot)

    assert again.proposal_id != first.proposal_id
    assert again.status == ProposalStatus.PROPOSED


def test_different_evidence_refs_are_a_different_proposal(tmp_path: Path) -> None:
    copilot = CareerCopilot(tmp_path / "sotuhire.db")
    payload = {"title": "Revisar currículo", "task_type": "document", "priority": "high"}
    first = copilot.propose("create_task", payload, reason="r", evidence_refs=["a"])
    second = copilot.propose("create_task", payload, reason="r", evidence_refs=["b"])

    assert first.proposal_id != second.proposal_id
    assert second.evidence_refs == ["b"]


# SH-AUD-010 --------------------------------------------------------------------


@pytest.mark.parametrize("due_at", ["amanhã", "2026-12-01T12:00:00", "2026-13-01T00:00:00Z"])
def test_create_task_rejects_ambiguous_or_invalid_due_at(tmp_path: Path, due_at: str) -> None:
    copilot = CareerCopilot(tmp_path / "sotuhire.db")

    with pytest.raises(ValueError):
        copilot.propose(
            "create_task", {"title": "Tarefa", "due_at": due_at}, reason="Validação de data."
        )


def test_create_task_normalizes_due_at_to_utc(tmp_path: Path) -> None:
    copilot = CareerCopilot(tmp_path / "sotuhire.db")

    proposal = copilot.propose(
        "create_task",
        {"title": "Tarefa", "due_at": "2026-12-01T12:00:00-03:00"},
        reason="Normalização.",
    )

    assert proposal.after_preview["due_at"] == "2026-12-01T15:00:00Z"


# SH-AUD-004 ---------------------------------------------------------------------


def _seed_application(database: Path) -> None:
    now = _now().isoformat()
    with connect_database(database) as connection:
        connection.execute(
            "INSERT INTO applications (id, created_at, updated_at) VALUES ('app-1', ?, ?)",
            (now, now),
        )


def test_fingerprint_changes_when_exposed_rankings_or_outcomes_change(tmp_path: Path) -> None:
    database = tmp_path / "sotuhire.db"
    engine = CareerStateEngine(database)
    baseline = engine.build().dependency_hash

    # Below the high-fit threshold: no count changes, but top_opportunities does.
    with connect_database(database) as connection:
        connection.execute(
            """INSERT INTO opportunity_rankings
            (ranking_id,opportunity_id,fit_score,confidence,evidence_coverage,ranking_version,
             created_at) VALUES ('r1','opp-1',40,0.5,0.2,'v1',?)""",
            (_now().isoformat(),),
        )
    after_ranking = engine.build()
    assert after_ranking.top_opportunities
    assert after_ranking.dependency_hash != baseline

    _seed_application(database)
    with connect_database(database) as connection:
        connection.execute(
            """INSERT INTO outcome_events (event_id,application_id,event_type,occurred_at,
            created_at) VALUES ('e1','app-1','response_received',?,?)""",
            (_now().isoformat(), _now().isoformat()),
        )
    after_outcome = engine.build()
    assert after_outcome.recent_outcomes
    assert after_outcome.dependency_hash != after_ranking.dependency_hash


def test_fingerprint_ignores_unexposed_edge_metadata(tmp_path: Path) -> None:
    repository = CopilotRepository(tmp_path / "sotuhire.db")
    repository.save_node(_node("project-x"))
    repository.save_node(_node("project-y"))
    edge = EvidenceEdge(
        edge_id="edge-x",
        source_id="project-x",
        target_id="project-y",
        relation_type=EvidenceRelationType.PROJECT_DEMONSTRATES_SKILL,
        confidence=0.3,
        created_at=_now(),
        updated_at=_now(),
    )
    repository.save_edge(edge)
    engine = CareerStateEngine(repository.database_path)
    before = engine.build().dependency_hash

    repository.save_edge(edge.model_copy(update={"confidence": 0.6, "updated_at": _now()}))

    assert engine.build().dependency_hash == before


# SH-AUD-014 ---------------------------------------------------------------------


def test_career_state_never_reports_healthy_for_inconsistent_database(tmp_path: Path) -> None:
    from modules.storage.migrations import MigrationError

    database = tmp_path / "sotuhire.db"
    engine = CareerStateEngine(database)
    assert engine.build().data_health == "healthy"
    with connect_database(database) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """INSERT INTO action_executions
            (execution_id,proposal_id,status,result,before_snapshot,after_snapshot,executed_at)
            VALUES ('x','missing-proposal','executed','{}','{}','{}',?)""",
            (_now().isoformat(),),
        )

    with pytest.raises(MigrationError, match="Foreign key"):
        engine.build()


# SH-NEW-003: overdue detection compares stored due_at text with UTC "now" ----------


def test_overdue_detection_is_correct_for_non_utc_deadlines(tmp_path: Path) -> None:
    from modules.career_actions.models import CareerTask

    database = tmp_path / "sotuhire.db"
    workflows = CareerWorkflowRepository(database)
    # Due one hour ago, expressed at UTC+14: the text "…+14:00" sorts *after* UTC now,
    # so a non-normalized store would report the task as not yet due.
    due = (_now() - timedelta(hours=1)).astimezone(timezone(timedelta(hours=14)))
    workflows.save_task(CareerTask(title="Prazo vencido", due_at=due))

    state = CareerStateEngine(database).build()

    assert state.overdue_tasks == 1
