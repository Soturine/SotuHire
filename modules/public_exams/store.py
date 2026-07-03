"""Atomic local JSON store for public exam notices."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from modules.core.text_utils import normalize_text

from .models import ExamNotice, utc_now


class PublicExamState(BaseModel):
    """Persisted public exam notice state."""

    model_config = ConfigDict(extra="forbid")

    notices: list[ExamNotice] = Field(default_factory=list)


class PublicExamStore:
    """Local-first atomic store for public exam notices."""

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        self.path = Path(path) if path is not None else base / "public_exams" / "notices.json"

    def load_state(self) -> PublicExamState:
        """Load state, tolerating missing or invalid JSON."""
        if not self.path.exists():
            return PublicExamState()
        try:
            return PublicExamState.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return PublicExamState()

    def save_state(self, state: PublicExamState) -> PublicExamState:
        """Persist state atomically."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self.path)
        return state

    def list_notices(self) -> list[ExamNotice]:
        """Return saved notices, newest first."""
        return sorted(
            self.load_state().notices,
            key=lambda notice: notice.updated_at,
            reverse=True,
        )

    def get_notice(self, notice_id: str) -> ExamNotice | None:
        """Return one notice by id."""
        return next(
            (notice for notice in self.load_state().notices if notice.notice_id == notice_id),
            None,
        )

    def save_notice(self, notice: ExamNotice) -> ExamNotice:
        """Insert or replace one reviewed notice."""
        state = self.load_state()
        saved = notice.model_copy(update={"status": "confirmed", "updated_at": utc_now()})
        for index, existing in enumerate(state.notices):
            if existing.notice_id == saved.notice_id:
                state.notices[index] = saved
                break
        else:
            state.notices.append(saved)
        self.save_state(state)
        return saved

    def delete_notice(self, notice_id: str) -> bool:
        """Delete one notice; return whether anything changed."""
        state = self.load_state()
        before = len(state.notices)
        state.notices = [notice for notice in state.notices if notice.notice_id != notice_id]
        if len(state.notices) == before:
            return False
        self.save_state(state)
        return True

    def list_roles(self) -> list[tuple[ExamNotice, str, str]]:
        """Return compact role tuples for integrations."""
        roles = []
        for notice in self.list_notices():
            for role in notice.roles:
                roles.append((notice, role.role_id, role.title))
        return roles

    def search_notices(self, query: str) -> list[ExamNotice]:
        """Search locally by title, organization, board or role."""
        needle = normalize_text(query)
        if not needle:
            return self.list_notices()
        matches = []
        for notice in self.list_notices():
            corpus = normalize_text(
                " ".join(
                    [
                        notice.title,
                        notice.organization,
                        notice.exam_board,
                        notice.source_name,
                        *[role.title for role in notice.roles],
                    ]
                )
            )
            if needle in corpus:
                matches.append(notice)
        return matches
