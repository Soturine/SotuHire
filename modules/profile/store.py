"""Local JSON store for Universal Career Profile data."""

from __future__ import annotations

import os
from pathlib import Path

from modules.profile.models import UniversalCareerProfile, UniversalCareerProfileState
from modules.storage.json_recovery import atomic_write_json, load_json


class UniversalCareerProfileStore:
    """Atomic local JSON store prepared for multiple local profiles."""

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        self.path = Path(path) if path is not None else base / "profile" / "profiles.json"

    def load_state(self) -> UniversalCareerProfileState:
        """Load all profile state, returning a default profile when missing."""
        state = load_json(
            self.path,
            validator=UniversalCareerProfileState.model_validate,
            default_factory=lambda: UniversalCareerProfileState(
                active_profile_id="default",
                profiles=[UniversalCareerProfile(profile_id="default")],
            ),
        )
        if not state.profiles:
            state.profiles.append(UniversalCareerProfile(profile_id=state.active_profile_id))
        return state

    def save_state(self, state: UniversalCareerProfileState) -> UniversalCareerProfileState:
        """Persist state atomically."""
        atomic_write_json(self.path, state.model_dump(mode="json"))
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
