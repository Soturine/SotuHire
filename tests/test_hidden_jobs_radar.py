from modules.search_intelligence import SearchStrategyInput, build_hidden_jobs_radar


def test_hidden_jobs_radar_is_strategic_and_never_scrapes():
    radar = build_hidden_jobs_radar(
        SearchStrategyInput(
            target_role="Desenvolvedor IoT Júnior",
            skills=["Python", "ESP32", "MQTT"],
        )
    )

    assert not radar.scraping_performed
    assert "Estágio em Software Embarcado" in radar.alternative_roles
    assert radar.manual_alerts
    assert radar.generic_job_risks
