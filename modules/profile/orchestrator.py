"""Assemble safe local profile context for AI-assisted workflows."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import ValidationError

from modules.profile.career_profile import CareerProfileStore
from modules.profile.context import ProfileContext, ProfileContextItem
from modules.profile.models import ProfileItem, UniversalCareerProfile
from modules.profile.schemas import CareerProfile
from modules.profile.store import UniversalCareerProfileStore


class ProfileContextOrchestrator:
    """Build a generic, evidence-backed profile context.

    The context deliberately avoids career-specific assumptions. It can represent
    technical, academic, healthcare, legal, industrial, artistic, service and
    transition paths without requiring GitHub, formal employment or a single
    professional domain.
    """

    def __init__(
        self,
        store: CareerProfileStore | None = None,
        universal_store: UniversalCareerProfileStore | None = None,
    ) -> None:
        self.legacy_store = store or CareerProfileStore(_default_legacy_profile_path())
        self.universal_store = universal_store or UniversalCareerProfileStore()

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

        universal_profile = self.universal_store.load_active()
        if _has_universal_profile_data(universal_profile):
            return _context_from_universal_profile(universal_profile, purpose=purpose)

        profile = self.legacy_store.load()
        return _context_from_legacy_profile(profile, purpose=purpose)


def _default_legacy_profile_path() -> Path:
    base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
    return base / "memory" / "career-profile.json"


def _has_universal_profile_data(profile: UniversalCareerProfile) -> bool:
    return any(
        [
            profile.display_name,
            profile.headline,
            profile.summary,
            profile.primary_domains,
            profile.secondary_domains,
            profile.career_moments,
            profile.target_roles,
            profile.target_seniority,
            profile.preferred_locations,
            profile.preferred_work_models,
            profile.preferred_contract_types,
            profile.items,
            profile.constraints,
        ]
    )


def _context_from_universal_profile(
    profile: UniversalCareerProfile,
    *,
    purpose: str,
) -> ProfileContext:
    items = [*profile.items, *profile.constraints]
    return ProfileContext(
        identity={
            "profile_id": profile.profile_id,
            "display_name": profile.display_name or "",
            "headline": profile.headline or "",
            "summary": profile.summary or "",
        },
        career_goals=list(profile.target_roles),
        education=_items_of_type(
            items,
            {
                "education",
                "technical_education",
                "higher_education",
                "postgraduate_education",
                "language_course",
                "free_course",
            },
        ),
        experiences=_items_of_type(
            items,
            {
                "professional_experience",
                "internship",
                "trainee",
                "volunteer_work",
                "freelance_work",
                "residency",
                "clinical_practice",
                "teaching_practice",
                "laboratory_practice",
                "field_work",
            },
        ),
        academic_experiences=_items_of_type(
            items,
            {"academic_experience", "research", "publication", "teaching_practice"},
        ),
        projects=_items_of_type(items, {"project", "portfolio"}),
        certifications_and_registries=_items_of_type(
            items,
            {"certification", "professional_registry", "license", "standard_or_norm"},
        ),
        skills=_items_of_type(
            items,
            {"technical_skill", "practical_skill", "soft_skill", "tool", "method"},
        ),
        languages=_items_of_type(items, {"language", "language_course"}),
        locations=list(profile.preferred_locations),
        preferences=[
            *profile.primary_domains,
            *profile.secondary_domains,
            *profile.preferred_work_models,
            *profile.preferred_contract_types,
        ],
        constraints=[item.title for item in profile.constraints],
        application_history_signals=[
            *[f"Objetivo: {role}" for role in profile.target_roles],
            *[f"Momento de carreira: {moment}" for moment in profile.career_moments],
            *[f"Senioridade alvo: {seniority}" for seniority in profile.target_seniority],
            f"Contexto montado para: {purpose}.",
        ],
    )


def _context_from_legacy_profile(profile: CareerProfile, *, purpose: str) -> ProfileContext:
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
        domain=area,
        source=source,
        evidence=title,
        confidence="medium",
        confirmed_by_user=False,
    )


def _items_of_type(items: list[ProfileItem], types: set[str]) -> list[ProfileContextItem]:
    return [_context_item(item) for item in items if item.type in types]


def _context_item(item: ProfileItem) -> ProfileContextItem:
    return ProfileContextItem(
        type=item.type,
        title=item.title,
        description=item.description,
        area=item.area,
        domain=item.domain,
        source=item.source,
        evidence=item.evidence,
        confidence=item.confidence,
        confirmed_by_user=item.confirmed_by_user,
    )
