"""Human feedback records linked to secret-free AI runs."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from modules.storage.ai_runs import sanitize_error_message
from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database

AiRating = Literal["useful", "partial", "not_useful"]
AiDecision = Literal["accepted", "edited", "rejected", "ignored"]


class AiFeedback(BaseModel):
    """One deletable human assessment of an AI-assisted result."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    task_id: str
    rating: AiRating
    decision: AiDecision
    edited: bool = False
    unsupported_claim: bool = False
    comment: str = Field(default="", max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AiFeedbackStore:
    """Persist feedback without model inputs, outputs or provider credentials."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def save(self, feedback: AiFeedback) -> AiFeedback:
        ensure_database(self.database_path)
        safe = feedback.model_copy(update={"comment": sanitize_error_message(feedback.comment)})
        with connect_database(self.database_path) as connection:
            run = connection.execute(
                "SELECT task_id FROM ai_runs WHERE run_id = ?", (safe.run_id,)
            ).fetchone()
            if run is None:
                raise LookupError("AI run not found")
            run_task = str(run["task_id"] or "")
            if run_task and run_task != safe.task_id:
                raise ValueError("Feedback task does not match AI run")
            connection.execute(
                """INSERT INTO ai_feedback
                (feedback_id, run_id, task_id, rating, decision, edited,
                 unsupported_claim, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    safe.feedback_id,
                    safe.run_id,
                    safe.task_id,
                    safe.rating,
                    safe.decision,
                    int(safe.edited or safe.decision == "edited"),
                    int(safe.unsupported_claim),
                    safe.comment,
                    safe.created_at.isoformat(),
                ),
            )
        return safe

    def list(
        self,
        *,
        run_id: str = "",
        task_id: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> list[AiFeedback]:
        ensure_database(self.database_path)
        clauses: list[str] = []
        parameters: list[object] = []
        if run_id:
            clauses.append("run_id = ?")
            parameters.append(run_id)
        if task_id:
            clauses.append("task_id = ?")
            parameters.append(task_id)
        query = "SELECT * FROM ai_feedback"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        parameters.extend([max(1, min(limit, 500)), max(0, offset)])
        with connect_database(self.database_path) as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
        return [AiFeedback.model_validate(dict(row)) for row in rows]

    def delete(self, feedback_id: str) -> bool:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM ai_feedback WHERE feedback_id = ?", (feedback_id,)
            )
        return cursor.rowcount > 0


__all__ = ["AiDecision", "AiFeedback", "AiFeedbackStore", "AiRating"]
