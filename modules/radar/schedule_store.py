"""Atomic local store for scheduled Radar state."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from modules.radar.schedule_models import LocalNotification, RadarSchedule, RadarScheduledRun

MAX_SCHEDULED_RUNS = 100
MAX_NOTIFICATIONS = 200


class RadarScheduleState(BaseModel):
    """Persisted local state for schedules, run history and notifications."""

    model_config = ConfigDict(extra="forbid")

    schedules: list[RadarSchedule] = Field(default_factory=list)
    scheduled_runs: list[RadarScheduledRun] = Field(default_factory=list)
    notifications: list[LocalNotification] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RadarScheduleStore:
    """Small atomic JSON store for scheduler data."""

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        self.path = Path(path) if path is not None else base / "radar" / "schedules.json"

    def load(self) -> RadarScheduleState:
        """Read scheduler state; corrupted files return an empty state with warning."""
        if not self.path.exists():
            return RadarScheduleState()
        try:
            return RadarScheduleState.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return RadarScheduleState(warnings=[f"Estado de agendamento reiniciado: {exc}"])

    def save(self, state: RadarScheduleState) -> RadarScheduleState:
        """Persist state with atomic replace and retention."""
        state.scheduled_runs = sorted(
            state.scheduled_runs,
            key=lambda item: item.started_at,
            reverse=True,
        )[:MAX_SCHEDULED_RUNS]
        state.notifications = sorted(
            state.notifications,
            key=lambda item: item.created_at,
            reverse=True,
        )[:MAX_NOTIFICATIONS]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self.path)
        return state
