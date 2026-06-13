from modules.scraping.robots import inspect_source_safety


def test_linkedin_public_mode_routes_to_authenticated_browser():
    safety = inspect_source_safety("https://www.linkedin.com/jobs/")

    assert not safety.allowed
    assert safety.robots_status == "bloqueado"
    assert "Navegador autenticado autorizado" in safety.warning
