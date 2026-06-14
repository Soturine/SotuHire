"""Build a persistent career profile from local structured evidence."""

from __future__ import annotations

from collections import Counter

from modules.core.text_utils import normalize_text
from modules.memory.schemas import CareerMemoryItem
from modules.profile.schemas import CareerProfile, InferredPreferences
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.schemas.user_preferences import UserPreferences

SENIORITIES = ("estagio", "trainee", "junior", "pleno", "senior", "lead")
MODALITIES = ("remote", "hybrid", "onsite", "remoto", "hibrido", "presencial")
CONTRACTS = ("clt", "pj", "estagio", "trainee", "temporario", "freelance")


def _unique(items: list[str], limit: int = 20) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))[:limit]


def _frequent_tags(items: list[CareerMemoryItem], limit: int = 15) -> list[str]:
    return [
        tag for tag, _ in Counter(tag for item in items for tag in item.tags).most_common(limit)
    ]


def _values_containing(items: list[CareerMemoryItem], terms: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for item in items:
        content = normalize_text(f"{item.title} {item.content}")
        values.extend(term for term in terms if term in content)
    return _unique(values)


def infer_preferences(items: list[CareerMemoryItem]) -> InferredPreferences:
    """Infer editable preferences from local facts and events."""
    opportunity_items = [
        item for item in items if item.kind in {"opportunity", "job_analysis", "tracker_event"}
    ]
    explicit_items = [item for item in items if item.kind == "preference"]
    role_titles = [
        item.title.removeprefix("Análise: ").split(" · ")[0]
        for item in opportunity_items
        if item.title
    ]
    companies = [item.title.split(" · ", 1)[1] for item in opportunity_items if " · " in item.title]
    preference_text = " ".join(item.content for item in explicit_items)
    return InferredPreferences(
        target_roles=_unique(role_titles, 8),
        modalities=_values_containing(items, MODALITIES),
        locations=_unique(
            [
                value.strip()
                for item in explicit_items
                if "localiza" in normalize_text(item.title)
                for value in item.content.split(",")
            ],
            8,
        ),
        contracts=_values_containing(items, CONTRACTS),
        seniorities=_values_containing(items, SENIORITIES),
        relevant_skills=_frequent_tags(items),
        target_companies=_unique(companies, 8),
    ).model_copy(
        update={
            "modalities": _unique(
                [
                    *(_values_containing(items, MODALITIES)),
                    *[term for term in MODALITIES if term in normalize_text(preference_text)],
                ]
            )
        }
    )


def build_career_profile(
    resume: ResumeProfileSchema,
    items: list[CareerMemoryItem],
    preferences: UserPreferences | None = None,
) -> CareerProfile:
    """Consolidate resume, memory, and explicit preferences."""
    explicit = preferences or UserPreferences()
    inferred = infer_preferences(items)
    gaps = [
        gap.strip()
        for item in items
        if item.kind == "job_analysis"
        for gap in item.content.partition("Gaps:")[2].split(",")
        if gap.strip()
    ]
    strengths = [
        strength.strip()
        for item in items
        if item.kind == "job_analysis"
        for strength in item.content.partition("Fortes:")[2].partition("Gaps:")[0].split(",")
        if strength.strip()
    ]
    likely_seniority = inferred.seniorities[0] if inferred.seniorities else None
    return CareerProfile(
        target_roles=inferred.target_roles,
        likely_seniority=likely_seniority,
        technical_skills=_unique([*resume.skills, *inferred.relevant_skills]),
        soft_skills=_unique(resume.soft_skills),
        education_summary=_unique(resume.education),
        experience_summary=_unique(resume.experiences),
        project_highlights=_unique(resume.projects),
        links=_unique(resume.links),
        preferred_modalities=_unique([*explicit.preferred_modalities, *inferred.modalities]),
        preferred_locations=_unique([*explicit.preferred_locations, *inferred.locations]),
        preferred_contracts=_unique([*explicit.accepted_contracts, *inferred.contracts]),
        target_companies=inferred.target_companies,
        recurring_gaps=_unique(gaps, 12),
        strengths=_unique(strengths, 12),
    )
