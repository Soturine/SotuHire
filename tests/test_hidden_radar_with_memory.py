from modules.profile import CareerProfile
from modules.search_intelligence import SearchStrategyInput, build_memory_search_plan


def test_hidden_radar_uses_projects_experience_and_skills_from_memory():
    profile = CareerProfile(
        target_roles=["Desenvolvedor IoT Júnior"],
        technical_skills=["Python", "ESP32", "IoT"],
        project_highlights=["Sistema embarcado industrial com ESP32"],
        experience_summary=["Processos técnicos industriais"],
    )

    plan = build_memory_search_plan(SearchStrategyInput(target_role=""), profile)

    assert "integradoras IoT" in plan.radar.target_company_ideas
    assert "empresas de automação" in plan.radar.target_company_ideas
    assert any("memória de carreira" in alert for alert in plan.radar.manual_alerts)
