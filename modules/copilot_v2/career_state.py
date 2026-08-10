"""Deterministic Career State and next-best-action engines."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database

from .models import CareerState, ConfidenceBreakdown, EvidenceNode, NextBestAction
from .repository import CopilotRepository


def utc_now() -> datetime:
    return datetime.now(UTC)


class NextBestActionEngine:
    """Create transparent candidates from explicit local facts and dates."""

    def candidates(
        self,
        *,
        confirmed: list[EvidenceNode],
        pending: list[EvidenceNode],
        counts: dict[str, int],
        now: datetime,
    ) -> list[NextBestAction]:
        raw: list[tuple[str, int, str, str, list[str], str, str, bool]] = []
        if counts["overdue_tasks"]:
            raw.append(
                (
                    "APPLICATION_FOLLOW_UP_DUE",
                    95,
                    "critical",
                    "Há tarefas vencidas que exigem revisão humana.",
                    [],
                    "Evita perder um prazo já registrado.",
                    "5–15 min",
                    True,
                )
            )
        if counts["upcoming_interviews"]:
            raw.append(
                (
                    "INTERVIEW_PREP_DUE",
                    90,
                    "high",
                    "Há entrevista agendada nos próximos sete dias.",
                    [],
                    "Cria espaço para preparação baseada em evidências.",
                    "30–60 min",
                    True,
                )
            )
        if pending:
            raw.append(
                (
                    "PROFILE_REVIEW_REQUIRED",
                    82,
                    "high",
                    f"{len(pending)} evidência(s) aguardam confirmação.",
                    [node.node_id for node in pending[:20]],
                    "Aumenta a cobertura sem transformar inferência em fato.",
                    "10–20 min",
                    False,
                )
            )
        projects = [node for node in confirmed if node.node_type == "project"]
        if projects and counts["portfolio_items"] == 0:
            raw.append(
                (
                    "PORTFOLIO_GAP",
                    72,
                    "medium",
                    "Projetos confirmados ainda não possuem item de portfólio.",
                    [node.node_id for node in projects[:10]],
                    "Torna projetos comprováveis e reutilizáveis.",
                    "30–90 min",
                    False,
                )
            )
        skills = [node for node in confirmed if node.node_type == "skill"]
        connected = counts["confirmed_skill_edges"]
        if len(skills) > connected:
            raw.append(
                (
                    "MISSING_CRITICAL_EVIDENCE",
                    78,
                    "high",
                    "Há skills confirmadas sem relação de demonstração confirmada.",
                    [node.node_id for node in skills[:20]],
                    "Explicita quais experiências ou projetos realmente comprovam cada skill.",
                    "15–30 min",
                    False,
                )
            )
        if counts["high_fit_opportunities"]:
            raw.append(
                (
                    "HIGH_FIT_OPPORTUNITY",
                    76,
                    "medium",
                    "Há oportunidades com fit determinístico alto e evidência suficiente.",
                    [],
                    "Prioriza revisão; não inicia candidatura automática.",
                    "10–20 min",
                    False,
                )
            )
        if counts["stale_artifacts"]:
            raw.append(
                (
                    "RESUME_STALE",
                    68,
                    "medium",
                    "Há evidências ou materiais marcados como obsoletos.",
                    [],
                    "Evita reutilizar material desatualizado.",
                    "15–30 min",
                    False,
                )
            )
        result = [
            NextBestAction(
                action_id=str(uuid5(NAMESPACE_URL, f"sotuhire:{kind}:{reason}")),
                type=kind,
                priority=priority,
                urgency=urgency,
                reason=reason,
                evidence_refs=refs,
                impact=impact,
                estimated_effort=effort,
                blocking=blocking,
                created_at=now,
                expires_at=now + timedelta(days=7),
            )
            for kind, priority, urgency, reason, refs, impact, effort, blocking in raw
        ]
        return sorted(result, key=lambda item: (-item.priority, item.action_id))


class CareerStateEngine:
    """Build a bounded, cacheable state from SQLite without provider inference."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = Path(database_path) if database_path else default_database_path()
        self.repository = CopilotRepository(self.database_path)
        self.actions = NextBestActionEngine()

    def build(self, *, profile_id: str = "", persist: bool = False) -> CareerState:
        ensure_database(self.database_path)
        now = utc_now()
        confirmed = self.repository.list_nodes(review_status="confirmed", limit=1_000)
        pending = self.repository.list_nodes(review_status="candidate", limit=1_000)
        with connect_database(self.database_path) as connection:
            counts = {
                "active_applications": self._scalar(
                    connection,
                    "SELECT COUNT(*) FROM applications WHERE status NOT IN ('rejected','withdrawn','archived')",
                ),
                "upcoming_interviews": self._scalar(
                    connection,
                    "SELECT COUNT(*) FROM interview_sessions WHERE status IN ('scheduled','preparing') AND scheduled_at >= ? AND scheduled_at <= ?",
                    (now.isoformat(), (now + timedelta(days=7)).isoformat()),
                ),
                "pending_followups": self._scalar(
                    connection,
                    "SELECT COUNT(*) FROM follow_up_drafts WHERE status IN ('draft','reviewed')",
                ),
                "overdue_tasks": self._scalar(
                    connection,
                    "SELECT COUNT(*) FROM career_tasks WHERE status IN ('pending','in_progress') AND due_at IS NOT NULL AND due_at < ?",
                    (now.isoformat(),),
                ),
                "portfolio_items": self._scalar(
                    connection,
                    "SELECT COUNT(*) FROM portfolio_items WHERE review_status != 'rejected'",
                ),
                "confirmed_skill_edges": self._scalar(
                    connection,
                    "SELECT COUNT(DISTINCT target_id) FROM evidence_edges WHERE review_status='confirmed' AND relation_type IN ('experience_demonstrates_skill','project_demonstrates_skill','certification_supports_skill')",
                ),
                "high_fit_opportunities": self._scalar(
                    connection,
                    "SELECT COUNT(*) FROM opportunity_rankings WHERE fit_score >= 75 AND evidence_coverage >= 0.5",
                ),
                "stale_artifacts": self._scalar(
                    connection,
                    "SELECT COUNT(*) FROM evidence_nodes WHERE review_status='stale' OR (stale_at IS NOT NULL AND stale_at <= ?)",
                    (now.isoformat(),),
                ),
            }
            top_rows = connection.execute(
                """SELECT opportunity_id,fit_score,confidence,evidence_coverage,created_at
                FROM opportunity_rankings ORDER BY fit_score DESC,created_at DESC LIMIT 5"""
            ).fetchall()
            outcome_rows = connection.execute(
                """SELECT event_id,event_type,created_at FROM outcome_events
                ORDER BY created_at DESC LIMIT 5"""
            ).fetchall()
        recommendations = self.actions.candidates(
            confirmed=confirmed, pending=pending, counts=counts, now=now
        )
        strengths = [
            node.title
            for node in confirmed
            if node.node_type in {"skill", "knowledge", "certification"}
        ][:20]
        academic = [
            node.title
            for node in confirmed
            if node.node_type
            in {"education", "research", "publication", "teaching", "extension_activity"}
        ][:20]
        goals = [node.title for node in confirmed if node.node_type == "career_goal"][:10]
        dependency_payload = {
            "confirmed": [(node.node_id, node.updated_at.isoformat()) for node in confirmed],
            "pending": [(node.node_id, node.updated_at.isoformat()) for node in pending],
            "counts": counts,
        }
        dependency_hash = hashlib.sha256(
            json.dumps(dependency_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        total = len(confirmed) + len(pending)
        coverage = len(confirmed) / total if total else 0.0
        state = CareerState(
            profile_summary=(
                f"{len(confirmed)} evidências confirmadas e {len(pending)} para revisar."
            ),
            career_goals=goals,
            current_focus=[item.type for item in recommendations[:3]],
            confirmed_strengths=strengths,
            evidence_gaps=[item.title for item in pending[:20]],
            portfolio_gaps=[
                item.reason for item in recommendations if item.type == "PORTFOLIO_GAP"
            ],
            academic_strengths=academic,
            active_applications=counts["active_applications"],
            upcoming_interviews=counts["upcoming_interviews"],
            pending_followups=counts["pending_followups"],
            overdue_tasks=counts["overdue_tasks"],
            stale_artifacts=counts["stale_artifacts"],
            top_opportunities=[dict(row) for row in top_rows],
            recent_outcomes=[dict(row) for row in outcome_rows],
            provider_health="explicit-check-required",
            data_health="healthy",
            recommendation_candidates=recommendations,
            confidence=ConfidenceBreakdown(data_coverage=coverage, rule_confidence=1.0),
            dependency_hash=dependency_hash,
            generated_at=now,
        )
        if persist:
            self.repository.save_career_state(
                profile_id, dependency_hash, state.model_dump(mode="json"), "manual"
            )
        return state

    @staticmethod
    def _scalar(connection: object, query: str, parameters: tuple[object, ...] = ()) -> int:
        row = connection.execute(query, parameters).fetchone()  # type: ignore[attr-defined]
        return int(row[0]) if row else 0
