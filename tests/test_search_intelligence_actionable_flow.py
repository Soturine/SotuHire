from modules.search_intelligence import SearchStrategyInput, build_search_intelligence_plan
from modules.ui.search_intelligence_page import actionable_source


def test_search_intelligence_sources_are_collectable():
    plan = build_search_intelligence_plan(SearchStrategyInput(target_role="Data Analyst"))
    source = actionable_source(plan.sources[0])

    assert source.enabled
    assert source.type in {"generic_public_page", "company_career_page"}
    assert source.url.startswith("https://")
