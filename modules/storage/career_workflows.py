"""Single-writer SQLite repositories for interview and career-action workflows."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from modules.career_actions import CareerPlan, CareerTask, Reminder
from modules.interviews import (
    FollowUpDraft,
    InterviewDraftAnswer,
    InterviewPreparation,
    InterviewQuestion,
    InterviewSession,
    StarStory,
)
from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database

ModelT = TypeVar("ModelT", bound=BaseModel)


class CareerWorkflowRepository:
    """Persist all new v7 workflow entities transactionally in SQLite."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def save_interview(self, value: InterviewSession) -> InterviewSession:
        self._ensure()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO interview_sessions
                (session_id, application_id, job_snapshot_id, resume_snapshot_id, profile_id,
                 evidence_scope_id, interview_type, scheduled_at, organization, role, status,
                 notes, payload, created_at, updated_at)
                VALUES (?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    application_id=excluded.application_id,
                    job_snapshot_id=excluded.job_snapshot_id,
                    resume_snapshot_id=excluded.resume_snapshot_id,
                    profile_id=excluded.profile_id,
                    evidence_scope_id=excluded.evidence_scope_id,
                    interview_type=excluded.interview_type,
                    scheduled_at=excluded.scheduled_at,
                    organization=excluded.organization,
                    role=excluded.role,
                    status=excluded.status,
                    notes=excluded.notes,
                    payload=excluded.payload,
                    updated_at=excluded.updated_at""",
                (
                    value.session_id,
                    value.application_id,
                    value.job_snapshot_id,
                    value.resume_snapshot_id,
                    value.profile_id,
                    value.evidence_scope_id,
                    value.interview_type,
                    value.scheduled_at.isoformat() if value.scheduled_at else None,
                    value.organization,
                    value.role,
                    value.status,
                    value.notes,
                    _json(value),
                    value.created_at.isoformat(),
                    value.updated_at.isoformat(),
                ),
            )
        return value

    def get_interview(self, session_id: str) -> InterviewSession | None:
        return self._get("interview_sessions", "session_id", session_id, InterviewSession)

    def list_interviews(self, *, limit: int = 200) -> list[InterviewSession]:
        return self._list("interview_sessions", InterviewSession, limit=limit)

    def save_preparation(self, value: InterviewPreparation) -> InterviewPreparation:
        self._ensure()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO interview_preparations
                (preparation_id, session_id, payload, review_status, dependency_hash,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    preparation_id=excluded.preparation_id,
                    payload=excluded.payload,
                    review_status=excluded.review_status,
                    dependency_hash=excluded.dependency_hash,
                    updated_at=excluded.updated_at""",
                (
                    value.preparation_id,
                    value.session_id,
                    _json(value),
                    value.review_status,
                    value.dependency_hash,
                    value.created_at.isoformat(),
                    value.updated_at.isoformat(),
                ),
            )
        return value

    def get_preparation(self, session_id: str) -> InterviewPreparation | None:
        self._ensure()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT payload FROM interview_preparations WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return _model(row, InterviewPreparation)

    def save_star_story(self, value: StarStory) -> StarStory:
        self._save_simple(
            "star_stories",
            "story_id",
            value.story_id,
            value,
            extra={"title": value.title, "review_status": value.review_status},
        )
        return value

    def list_star_stories(self, *, limit: int = 200) -> list[StarStory]:
        return self._list("star_stories", StarStory, limit=limit)

    def save_question(self, value: InterviewQuestion) -> InterviewQuestion:
        self._save_simple(
            "interview_questions",
            "question_id",
            value.question_id,
            value,
            extra={
                "session_id": value.session_id or None,
                "category": value.category,
                "question": value.question,
                "review_status": value.review_status,
            },
        )
        return value

    def list_questions(self, *, session_id: str = "", limit: int = 200) -> list[InterviewQuestion]:
        return self._list(
            "interview_questions",
            InterviewQuestion,
            limit=limit,
            where=("session_id", session_id) if session_id else None,
        )

    def save_answer(self, value: InterviewDraftAnswer) -> InterviewDraftAnswer:
        self._save_simple(
            "interview_draft_answers",
            "answer_id",
            value.answer_id,
            value,
            extra={"question_id": value.question_id, "status": value.status},
        )
        return value

    def list_answers(
        self, *, question_id: str = "", limit: int = 200
    ) -> list[InterviewDraftAnswer]:
        return self._list(
            "interview_draft_answers",
            InterviewDraftAnswer,
            limit=limit,
            where=("question_id", question_id) if question_id else None,
        )

    def save_follow_up(self, value: FollowUpDraft) -> FollowUpDraft:
        self._save_simple(
            "follow_up_drafts",
            "follow_up_id",
            value.follow_up_id,
            value,
            extra={
                "application_id": value.application_id or None,
                "interview_session_id": value.interview_session_id or None,
                "follow_up_type": value.follow_up_type,
                "status": value.status,
            },
        )
        return value

    def list_follow_ups(self, *, limit: int = 200) -> list[FollowUpDraft]:
        return self._list("follow_up_drafts", FollowUpDraft, limit=limit)

    def save_task(self, value: CareerTask) -> CareerTask:
        self._save_simple(
            "career_tasks",
            "task_id",
            value.task_id,
            value,
            extra={
                "task_type": value.task_type,
                "title": value.title,
                "status": value.status,
                "priority": value.priority,
                "due_at": value.due_at.isoformat() if value.due_at else None,
                "completed_at": (value.completed_at.isoformat() if value.completed_at else None),
            },
        )
        return value

    def list_tasks(self, *, limit: int = 500) -> list[CareerTask]:
        return self._list("career_tasks", CareerTask, limit=limit)

    def save_reminder(self, value: Reminder) -> Reminder:
        self._save_simple(
            "reminders",
            "reminder_id",
            value.reminder_id,
            value,
            extra={
                "task_id": value.task_id or None,
                "remind_at": value.remind_at.isoformat(),
                "status": value.status,
            },
        )
        return value

    def list_reminders(self, *, limit: int = 500) -> list[Reminder]:
        return self._list("reminders", Reminder, limit=limit)

    def save_career_plan(self, value: CareerPlan) -> CareerPlan:
        self._save_simple(
            "career_plans",
            "plan_id",
            value.plan_id,
            value,
            extra={
                "profile_id": value.profile_id,
                "title": value.title,
                "status": value.status,
                "dependency_hash": value.dependency_hash,
            },
        )
        return value

    def list_career_plans(self, *, limit: int = 100) -> list[CareerPlan]:
        return self._list("career_plans", CareerPlan, limit=limit)

    def _ensure(self) -> None:
        ensure_database(self.database_path)

    def _save_simple(
        self,
        table: str,
        id_column: str,
        entity_id: str,
        value: BaseModel,
        *,
        extra: dict[str, object],
    ) -> None:
        allowed = _TABLE_COLUMNS[table]
        if id_column not in allowed or not set(extra).issubset(allowed):
            raise ValueError("Contrato interno de persistencia invalido.")
        columns = [id_column, *extra, "payload", "created_at", "updated_at"]
        serialized = value.model_dump(mode="json")
        parameters = [
            entity_id,
            *extra.values(),
            _json(value),
            str(serialized["created_at"]),
            str(serialized["updated_at"]),
        ]
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(
            f"{column}=excluded.{column}"
            for column in columns
            if column not in {id_column, "created_at"}
        )
        self._ensure()
        with connect_database(self.database_path) as connection:
            connection.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
                f"ON CONFLICT({id_column}) DO UPDATE SET {updates}",
                parameters,
            )

    def _get(
        self,
        table: str,
        id_column: str,
        entity_id: str,
        model: type[ModelT],
    ) -> ModelT | None:
        if id_column not in _TABLE_COLUMNS[table]:
            raise ValueError("Contrato interno de leitura invalido.")
        self._ensure()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                f"SELECT payload FROM {table} WHERE {id_column} = ?", (entity_id,)
            ).fetchone()
        return _model(row, model)

    def _list(
        self,
        table: str,
        model: type[ModelT],
        *,
        limit: int,
        where: tuple[str, str] | None = None,
    ) -> list[ModelT]:
        self._ensure()
        bounded = max(1, min(limit, 2_000))
        query = f"SELECT payload FROM {table}"
        parameters: tuple[object, ...] = ()
        if where:
            column, value = where
            if column not in _TABLE_COLUMNS[table]:
                raise ValueError("Contrato interno de filtro invalido.")
            query += f" WHERE {column} = ?"
            parameters = (value,)
        query += " ORDER BY updated_at DESC LIMIT ?"
        parameters = (*parameters, bounded)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [value for row in rows if (value := _model(row, model)) is not None]


_TABLE_COLUMNS: dict[str, frozenset[str]] = {
    "interview_sessions": frozenset(
        {
            "session_id",
            "application_id",
            "job_snapshot_id",
            "resume_snapshot_id",
            "profile_id",
            "evidence_scope_id",
            "interview_type",
            "scheduled_at",
            "organization",
            "role",
            "status",
            "notes",
        }
    ),
    "star_stories": frozenset({"story_id", "title", "review_status"}),
    "interview_questions": frozenset(
        {"question_id", "session_id", "category", "question", "review_status"}
    ),
    "interview_draft_answers": frozenset({"answer_id", "question_id", "status"}),
    "follow_up_drafts": frozenset(
        {
            "follow_up_id",
            "application_id",
            "interview_session_id",
            "follow_up_type",
            "status",
        }
    ),
    "career_tasks": frozenset(
        {
            "task_id",
            "task_type",
            "title",
            "status",
            "priority",
            "due_at",
            "completed_at",
        }
    ),
    "reminders": frozenset({"reminder_id", "task_id", "remind_at", "status"}),
    "career_plans": frozenset({"plan_id", "profile_id", "title", "status", "dependency_hash"}),
}


def _json(value: BaseModel) -> str:
    return value.model_dump_json()


def _model(row: sqlite3.Row | None, model: type[ModelT]) -> ModelT | None:
    if row is None:
        return None
    return model.model_validate(json.loads(row["payload"]))


__all__ = ["CareerWorkflowRepository"]
