"""Persist the consolidated local career profile."""

from __future__ import annotations

from pathlib import Path

from modules.profile.schemas import CareerProfile


class CareerProfileStore:
    """Small local JSON profile store."""

    def __init__(self, path: str | Path = "data/memory/career-profile.json") -> None:
        self.path = Path(path)

    def save(self, profile: CareerProfile) -> CareerProfile:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self.path)
        return profile

    def load(self) -> CareerProfile:
        if not self.path.exists():
            return CareerProfile()
        try:
            return CareerProfile.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return CareerProfile()

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
