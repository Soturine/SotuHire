"""Assemble safe local profile context for AI-assisted workflows."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import ValidationError

from modules.profile.career_profile import CareerProfileStore
from modules.profile.context import ProfileContext, ProfileContextItem
from modules.profile.schemas import CareerProfile


class ProfileContextOrchestrator:
    """Build a generic, evidence-backed profile context.

    The context deliberately avoids career-specific assumptions. It can represent
    technical, academic, healthcare, legal, industrial, artistic, service and
    transition paths without requiring GitHub, formal employment or a single
    professional domain.
    """

    def __init__(self, store: CareerProfileStore | None = None) -> None:
        self.store = store or CareerProfileStore(_default_profile_path())

    def build_context(
        self,
        *,
        purpose: str = "generic",
        override: dict[str, object] | None = None,
    ) -> ProfileContext:
        """Return a compact context from local evidence or a validated override."""
        if override is not None:
            try:
                return ProfileContext.model_validate(override)
            except ValidationError as exc:
                raise ValueError("Contexto de perfil invalido.") from exc

        profile = self.store.load()
        return _context_from_profile(profile, purpose=purpose)


def _default_profile_path() -> Path:
    base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
    return base / "memory" / "career-profile.json"


def _context_from_profile(profile: CareerProfile, *, purpose: str) -> ProfileContext:
    skills = [
        *[
            _item("skill", skill, area="technical", source="career_profile")
            for skill in profile.technical_skills
        ],
        *[
            _item("skill", skill, area="medium", source="career_profile")
            for skill in profile.medium_skills
        ],
        *[
            _item("skill", skill, area="soft", source="career_profile")
            for skill in profile.soft_skills
        ],
    ]
    return ProfileContext(
        career_goals=list(profile.target_roles),
        education=[
            _item("education", entry, source="career_profile")
            for entry in profile.education_summary
        ],
        experiences=[
            _item("experience", entry, source="career_profile")
            for entry in profile.experience_summary
        ],
        projects=[
            _item("project", entry, source="career_profile")
            for entry in [*profile.project_highlights, *profile.links]
        ],
        skills=skills,
        locations=list(profile.preferred_locations),
        preferences=[
            *profile.preferred_modalities,
            *profile.preferred_contracts,
            *profile.target_companies,
            *profile.recommended_sectors,
        ],
        constraints=list(profile.recurring_gaps),
        application_history_signals=[
            *[f"Forca local: {item}" for item in profile.strengths],
            *[f"Lacuna recorrente: {item}" for item in profile.recurring_gaps],
            *(
                [f"Senioridade provavel: {profile.likely_seniority}"]
                if profile.likely_seniority
                else []
            ),
            f"Contexto montado para: {purpose}.",
        ],
    )


def _item(
    item_type: str,
    title: str,
    *,
    area: str | None = None,
    source: str | None = None,
) -> ProfileContextItem:
    return ProfileContextItem(
        type=item_type,
        title=title,
        area=area,
        source=source,
        evidence=title,
        confidence="medium",
        confirmed_by_user=False,
    )
