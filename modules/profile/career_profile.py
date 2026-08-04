"""Persist the consolidated local career profile."""

from __future__ import annotations

from pathlib import Path

from modules.profile.schemas import CareerProfile
from modules.storage.json_recovery import atomic_write_json, load_json


class CareerProfileStore:
    """Small local JSON profile store."""

    def __init__(self, path: str | Path = "data/memory/career-profile.json") -> None:
        self.path = Path(path)

    def save(self, profile: CareerProfile) -> CareerProfile:
        atomic_write_json(self.path, profile.model_dump(mode="json"))
        return profile

    def load(self) -> CareerProfile:
        return load_json(
            self.path,
            validator=CareerProfile.model_validate,
            default_factory=CareerProfile,
        )

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
