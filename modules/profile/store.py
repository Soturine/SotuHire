"""Local JSON store for Universal Career Profile data."""

from __future__ import annotations

import os
from pathlib import Path

from modules.profile.models import UniversalCareerProfile, UniversalCareerProfileState


class UniversalCareerProfileStore:
    """Atomic local JSON store prepared for multiple local profiles."""

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        self.path = Path(path) if path is not None else base / "profile" / "profiles.json"

    def load_state(self) -> UniversalCareerProfileState:
        """Load all profile state, returning a default profile when missing."""
        if not self.path.exists():
            return UniversalCareerProfileState(
                active_profile_id="default",
                profiles=[UniversalCareerProfile(profile_id="default")],
            )
        try:
            state = UniversalCareerProfileState.model_validate_json(
                self.path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            state = UniversalCareerProfileState()
        if not state.profiles:
            state.profiles.append(UniversalCareerProfile(profile_id=state.active_profile_id))
        return state

    def save_state(self, state: UniversalCareerProfileState) -> UniversalCareerProfileState:
        """Persist state atomically."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self.path)
        return state

    def load_active(self) -> UniversalCareerProfile:
        """Return the active profile."""
        state = self.load_state()
        profile = next(
            (item for item in state.profiles if item.profile_id == state.active_profile_id),
            None,
        )
        if profile is None:
            profile = UniversalCareerProfile(profile_id=state.active_profile_id)
            state.profiles.append(profile)
            self.save_state(state)
        return profile

    def save_active(self, profile: UniversalCareerProfile) -> UniversalCareerProfile:
        """Save the active profile inside the state document."""
        state = self.load_state()
        state.active_profile_id = profile.profile_id
        for index, existing in enumerate(state.profiles):
            if existing.profile_id == profile.profile_id:
                state.profiles[index] = profile
                break
        else:
            state.profiles.append(profile)
        self.save_state(state)
        return profile
