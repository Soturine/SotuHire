"""Atomic local store for scheduled Radar state."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from modules.radar.schedule_models import LocalNotification, RadarSchedule, RadarScheduledRun
from modules.storage.json_recovery import atomic_write_json, load_json

DEFAULT_MAX_SCHEDULED_RUNS = 100
DEFAULT_MAX_NOTIFICATIONS = 200


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
        """Read scheduler state or fail explicitly after quarantine."""
        return load_json(
            self.path,
            validator=RadarScheduleState.model_validate,
            default_factory=RadarScheduleState,
        )

    def save(self, state: RadarScheduleState) -> RadarScheduleState:
        """Persist state with atomic replace and retention."""
        state.scheduled_runs = sorted(
            state.scheduled_runs,
            key=lambda item: item.started_at,
            reverse=True,
        )[: _retention("SOTUHIRE_RADAR_MAX_SCHEDULED_RUNS", DEFAULT_MAX_SCHEDULED_RUNS)]
        state.notifications = sorted(
            state.notifications,
            key=lambda item: item.created_at,
            reverse=True,
        )[: _retention("SOTUHIRE_RADAR_MAX_NOTIFICATIONS", DEFAULT_MAX_NOTIFICATIONS)]
        atomic_write_json(self.path, state.model_dump(mode="json"))
        return state


def _retention(variable: str, default: int) -> int:
    try:
        return max(10, min(int(os.getenv(variable, str(default))), 10_000))
    except ValueError:
        return default
