"""Atomic local JSON store for public exam notices."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from modules.core.entity_identity import merge_source_refs, public_exam_identity
from modules.core.text_utils import normalize_text
from modules.storage.snapshots import PublicExamSnapshot, SnapshotStore

from .models import ExamNotice, ExamRequirement, ExamRole, ExamSubject, utc_now


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
        identity = _notice_identity(notice)
        duplicate = next(
            (
                existing
                for existing in state.notices
                if existing.notice_id != notice.notice_id and _notice_identity(existing) == identity
            ),
            None,
        )
        if duplicate is not None:
            saved = notice.model_copy(
                update={
                    "notice_id": duplicate.notice_id,
                    "created_at": duplicate.created_at,
                    "status": "confirmed",
                    "updated_at": utc_now(),
                    "identity_key": identity,
                    "source_refs": merge_source_refs(
                        duplicate.source_refs or [duplicate.source_url],
                        notice.source_refs or [notice.source_url],
                    ),
                    "merged_notice_ids": merge_source_refs(
                        duplicate.merged_notice_ids,
                        [notice.notice_id],
                    ),
                    "deduplication_reason": (
                        "Mesmo edital por URL normalizada, numero oficial ou conteudo."
                    ),
                    "roles": _merge_roles(duplicate.roles, notice.roles),
                    "general_requirements": _merge_requirements(
                        duplicate.general_requirements,
                        notice.general_requirements,
                    ),
                    "subjects": _merge_subjects(duplicate.subjects, notice.subjects),
                    "documents": merge_source_refs(duplicate.documents, notice.documents),
                    "locations": merge_source_refs(duplicate.locations, notice.locations),
                    "warnings": list(
                        dict.fromkeys(
                            [
                                *duplicate.warnings,
                                *notice.warnings,
                                "Edital duplicado consolidado com fontes preservadas.",
                            ]
                        )
                    ),
                }
            )
        else:
            saved = notice.model_copy(
                update={
                    "status": "confirmed",
                    "updated_at": utc_now(),
                    "identity_key": identity,
                    "source_refs": merge_source_refs(
                        notice.source_refs,
                        [notice.source_url],
                    ),
                }
            )
        for index, existing in enumerate(state.notices):
            if existing.notice_id == saved.notice_id:
                state.notices[index] = saved
                break
        else:
            state.notices.append(saved)
        self.save_state(state)
        self._snapshot_notice(saved)
        return saved

    def _snapshot_notice(self, notice: ExamNotice) -> None:
        """Keep the exact reviewed edital and each role as immutable history."""
        data_root = (
            self.path.parent.parent if self.path.parent.name == "public_exams" else self.path.parent
        )
        snapshots = SnapshotStore(data_root / "sotuhire.db")
        timeline: list[dict[str, Any] | str] = [notice.timeline.model_dump(mode="json")]
        snapshots.create_public_exam(
            PublicExamSnapshot(
                notice_id=notice.notice_id,
                raw_text=notice.raw_text,
                structured_notice=notice.model_dump(mode="json"),
                requirements=[item.description for item in notice.general_requirements],
                timeline=timeline,
            )
        )
        for role in notice.roles:
            snapshots.create_public_exam(
                PublicExamSnapshot(
                    notice_id=notice.notice_id,
                    role_id=role.role_id,
                    raw_text=notice.raw_text,
                    structured_notice={
                        "notice": notice.model_dump(mode="json"),
                        "role": role.model_dump(mode="json"),
                    },
                    requirements=[item.description for item in role.requirements],
                    timeline=timeline,
                )
            )

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


def _notice_identity(notice: ExamNotice) -> str:
    return notice.identity_key or public_exam_identity(
        source_url=notice.source_url,
        notice_number=notice.notice_number,
        organization=notice.organization,
        exam_board=notice.exam_board,
        title=notice.title,
        raw_text=notice.raw_text,
    )


def _merge_roles(current: list[ExamRole], incoming: list[ExamRole]) -> list[ExamRole]:
    merged = list(current)
    keys = {
        normalize_text(f"{role.title} {role.area} {role.level}"): index
        for index, role in enumerate(merged)
    }
    for role in incoming:
        key = normalize_text(f"{role.title} {role.area} {role.level}")
        index = keys.get(key)
        if index is None:
            keys[key] = len(merged)
            merged.append(role)
            continue
        existing = merged[index]
        merged[index] = role.model_copy(
            update={
                "role_id": existing.role_id,
                "requirements": _merge_requirements(existing.requirements, role.requirements),
                "subjects": _merge_subjects(existing.subjects, role.subjects),
                "stages": merge_source_refs(existing.stages, role.stages),
            }
        )
    return merged


def _merge_requirements(
    current: list[ExamRequirement], incoming: list[ExamRequirement]
) -> list[ExamRequirement]:
    merged = list(current)
    seen = {normalize_text(item.description) for item in merged if item.description}
    for item in incoming:
        key = normalize_text(item.description)
        if key and key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def _merge_subjects(current: list[ExamSubject], incoming: list[ExamSubject]) -> list[ExamSubject]:
    merged = list(current)
    seen = {normalize_text(item.name) for item in merged if item.name}
    for item in incoming:
        key = normalize_text(item.name)
        if key and key not in seen:
            seen.add(key)
            merged.append(item)
    return merged
