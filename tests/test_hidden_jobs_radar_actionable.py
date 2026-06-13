from modules.search_intelligence import SearchStrategyInput, build_hidden_jobs_radar


def test_hidden_radar_generates_actionable_public_career_source():
    radar = build_hidden_jobs_radar(
        SearchStrategyInput(target_role="Backend", target_companies=["example.com"])
    )

    assert radar.actionable_sources
    assert radar.actionable_sources[0].url == "https://example.com/careers"
    assert not radar.scraping_performed
