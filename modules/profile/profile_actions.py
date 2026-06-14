"""Pure actions for applying, editing, and exporting a career profile."""

from __future__ import annotations

from modules.profile.schemas import CareerProfile


def profile_analysis_defaults(profile: CareerProfile) -> dict[str, object]:
    """Return session-compatible defaults derived from a reviewed profile."""
    return {
        "preferred_modalities": list(profile.preferred_modalities),
        "preferred_locations": ", ".join(profile.preferred_locations),
        "accepted_contracts": list(profile.preferred_contracts),
        "target_levels": [profile.likely_seniority] if profile.likely_seniority else [],
        "search_target_role": profile.target_roles[0] if profile.target_roles else "",
        "search_target_companies": ", ".join(profile.target_companies),
    }


def edit_career_profile(profile: CareerProfile, **changes: object) -> CareerProfile:
    """Validate explicit user edits without mutating the original profile."""
    return CareerProfile.model_validate(profile.model_copy(update=changes))


def export_career_profile(profile: CareerProfile) -> str:
    """Return a portable JSON representation of the profile."""
    return profile.model_dump_json(indent=2)
