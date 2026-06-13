from modules.search_intelligence import SearchStrategyInput, build_search_queries


def test_query_builder_uses_role_skills_location_and_modality():
    strategy = SearchStrategyInput(
        target_role="Desenvolvedor Backend Júnior",
        skills=["Python", "FastAPI", "Docker"],
        location="São Paulo",
        modality="remote",
        seniority="junior",
    )

    queries = build_search_queries(strategy)

    assert queries
    assert any("Python" in query for query in queries)
    assert any("remoto" in query for query in queries)
    assert any("site:gupy.io" in query for query in queries)
