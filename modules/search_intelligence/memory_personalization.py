"""Personalize search intelligence with the local career profile."""

from __future__ import annotations

from modules.core.text_utils import normalize_text
from modules.profile.schemas import CareerProfile
from modules.search_intelligence.query_builder import build_search_queries
from modules.search_intelligence.schemas import SearchIntelligencePlan, SearchStrategyInput
from modules.search_intelligence.source_plan import build_search_intelligence_plan

SECTOR_SIGNALS = {
    "iot": ["empresas de automação", "integradoras IoT", "software houses industriais"],
    "esp32": ["integradoras IoT", "empresas de sistemas embarcados"],
    "industrial": ["empresas aeroespaciais", "empresas de automação", "consultorias industriais"],
    "dados": ["consultorias de dados", "times de BI", "empresas orientadas a analytics"],
    "python": ["software houses Python", "consultorias de dados", "startups backend"],
}


def personalize_search_strategy(
    strategy: SearchStrategyInput,
    profile: CareerProfile,
) -> SearchStrategyInput:
    """Merge explicit search intent with locally inferred profile signals."""
    return strategy.model_copy(
        update={
            "target_role": strategy.target_role
            or (profile.target_roles[0] if profile.target_roles else ""),
            "skills": list(dict.fromkeys([*strategy.skills, *profile.technical_skills]))[:12],
            "location": strategy.location
            or (profile.preferred_locations[0] if profile.preferred_locations else ""),
            "modality": strategy.modality
            or (profile.preferred_modalities[0] if profile.preferred_modalities else ""),
            "seniority": strategy.seniority or profile.likely_seniority or "",
            "target_companies": list(
                dict.fromkeys([*strategy.target_companies, *profile.target_companies])
            )[:12],
            "contract": strategy.contract
            or (profile.preferred_contracts[0] if profile.preferred_contracts else ""),
        }
    )


def memory_sector_suggestions(profile: CareerProfile) -> list[str]:
    """Suggest sectors from projects, experiences, and strong skills."""
    corpus = normalize_text(
        " ".join(
            [
                *profile.technical_skills,
                *profile.project_highlights,
                *profile.experience_summary,
            ]
        )
    )
    suggestions = [
        suggestion
        for signal, values in SECTOR_SIGNALS.items()
        if signal in corpus
        for suggestion in values
    ]
    return list(dict.fromkeys(suggestions))


def build_memory_search_plan(
    strategy: SearchStrategyInput,
    profile: CareerProfile,
) -> SearchIntelligencePlan:
    """Build search queries and hidden radar personalized by local memory."""
    personalized = personalize_search_strategy(strategy, profile)
    plan = build_search_intelligence_plan(personalized)
    queries = build_search_queries(personalized, limit=12)
    sectors = memory_sector_suggestions(profile)
    radar = plan.radar.model_copy(
        update={
            "target_company_ideas": list(
                dict.fromkeys(
                    [*profile.target_companies, *sectors, *plan.radar.target_company_ideas]
                )
            ),
            "manual_alerts": [
                *plan.radar.manual_alerts,
                *[f"Explorar {sector} com base na sua memória de carreira." for sector in sectors],
            ],
        }
    )
    return plan.model_copy(update={"queries": queries, "radar": radar})
