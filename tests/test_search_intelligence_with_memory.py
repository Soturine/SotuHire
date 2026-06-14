from modules.profile import CareerProfile
from modules.search_intelligence import SearchStrategyInput, build_memory_search_plan


def test_search_intelligence_uses_memory_profile():
    profile = CareerProfile(
        target_roles=["Desenvolvedor Backend Júnior"],
        technical_skills=["Python", "FastAPI"],
        preferred_modalities=["remote"],
        preferred_locations=["São Paulo"],
        target_companies=["example.com"],
    )

    plan = build_memory_search_plan(SearchStrategyInput(target_role=""), profile)

    assert any("Python" in query for query in plan.queries)
    assert any("remoto" in query for query in plan.queries)
    assert any("example.com" in query for query in plan.queries)
