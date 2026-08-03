from __future__ import annotations

from pathlib import Path

from apps.api.config import ApiSettings
from apps.api.main import create_app
from apps.api.services.tracker import TrackerService, get_tracker_service
from fastapi.testclient import TestClient
from modules.storage.local_store import LocalStore
from modules.tracker.job_tracker import JobTracker

RESUME_TEXT = """Pessoa Ficticia
pessoa@example.invalid
LinkedIn: https://linkedin.com/in/pessoa-ficticia
GitHub: https://github.com/example
Resumo: Desenvolvedora backend com Python, FastAPI e SQL.
Skills: Python, FastAPI, SQL, Git
Experiencia: Desenvolvedora Python - 2022 - atual
Projetos: API de vagas com FastAPI, testes Pytest e PostgreSQL.
Formacao: Tecnologia em Analise e Desenvolvimento de Sistemas
"""

JOB_TEXT = """Cargo: Desenvolvedor Backend Python
Empresa: Empresa Ficticia
Localizacao: Remoto
Modalidade remota, CLT, nivel junior.
Requisitos: Python, FastAPI, SQL, Git e Docker.
Desejavel: Pytest e PostgreSQL.
"""

TEST_API_TOKEN = "test-only-local-api-token-with-at-least-32-characters"


def api_test_settings() -> ApiSettings:
    return ApiSettings(installation_token=TEST_API_TOKEN)


def authenticated_test_client(app=None) -> TestClient:
    resolved_app = app or create_app(api_test_settings())
    return TestClient(
        resolved_app,
        base_url="http://127.0.0.1:8787",
        headers={"X-SotuHire-Token": TEST_API_TOKEN},
    )


def api_client() -> TestClient:
    return authenticated_test_client()


def api_client_with_tracker(tmp_path: Path) -> TestClient:
    service = TrackerService(JobTracker(LocalStore(tmp_path / "history.json")))
    app = create_app(api_test_settings())
    app.dependency_overrides[get_tracker_service] = lambda: service
    return authenticated_test_client(app)
