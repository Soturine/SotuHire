"""Deterministic completeness score for the local career profile."""

from __future__ import annotations

from modules.profile.schemas import CareerProfile


def profile_completeness_score(profile: CareerProfile) -> int:
    """Return a 0-100 score based on useful, evidence-backed profile sections."""
    sections: list[tuple[bool, int]] = [
        (bool(profile.target_roles), 15),
        (bool(profile.technical_skills), 20),
        (bool(profile.soft_skills), 5),
        (bool(profile.education_summary), 10),
        (bool(profile.experience_summary), 15),
        (bool(profile.project_highlights), 15),
        (bool(profile.links), 5),
        (
            bool(
                profile.preferred_modalities
                or profile.preferred_locations
                or profile.preferred_contracts
            ),
            10,
        ),
        (bool(profile.strengths or profile.recurring_gaps), 5),
    ]
    return sum(weight for present, weight in sections if present)
