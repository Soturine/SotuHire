from typing import Any, cast

from modules.local_api import LocalCompanionApp, LocalCompanionService
from modules.memory import CareerMemory, MemoryStore
from modules.portfolio import ProjectAnalysisStore


def test_connected_sotuhire_mode_saves_full_report_and_evidence(tmp_path):
    memory = CareerMemory(MemoryStore(tmp_path / "memory.jsonl"))
    service = LocalCompanionService(
        memory=memory,
        project_store=ProjectAnalysisStore(tmp_path / "projects.jsonl"),
    )
    app = LocalCompanionApp(service)
    body = (
        b'{"url":"https://github.com/example/atlas","owner":"example","repo":"atlas",'
        b'"title":"Atlas","page_type":"github_repo","readme_text":"Install and usage",'
        b'"files_sampled":["README.md","src/api.py","tests/test_api.py"],'
        b'"commit_messages":["feat: add API"],"languages":["Python"]}'
    )

    status, payload = app.handle("POST", "/capture/repo-analysis", body=body)
    response = cast(dict[str, Any], payload)

    assert status == 200
    assert response["saved_to_memory"] is True
    assert cast(dict[str, Any], response["report"])["overall_score"] > 0
    assert service.project_store.list()
    assert memory.store.list_memory_items(kind="project_evidence")


def test_connected_mode_consumes_extension_ai_report_without_changing_local_scores(tmp_path):
    memory = CareerMemory(MemoryStore(tmp_path / "memory.jsonl"))
    service = LocalCompanionService(
        memory=memory,
        project_store=ProjectAnalysisStore(tmp_path / "projects.jsonl"),
    )
    body = (
        b'{"url":"https://github.com/example/atlas","owner":"example","repo":"atlas",'
        b'"title":"Atlas","page_type":"github_repo","languages":["Python"],'
        b'"analysis_result":{"extension_ai_report":{"provider_used":"openai",'
        b'"summary":"Analise externa baseada no README publico.",'
        b'"strengths":["Testes publicos"],"stack":["FastAPI"]}}}'
    )

    baseline_status, baseline_payload = LocalCompanionApp(service).handle(
        "POST",
        "/capture/repo-analysis",
        body=(
            b'{"url":"https://github.com/example/baseline","owner":"example",'
            b'"repo":"baseline","title":"Atlas","page_type":"github_repo",'
            b'"languages":["Python"]}'
        ),
    )
    status, payload = LocalCompanionApp(service).handle("POST", "/capture/repo-analysis", body=body)

    baseline_report = cast(dict[str, Any], baseline_payload)["report"]
    report = cast(dict[str, Any], payload)["report"]
    assert baseline_status == status == 200
    assert report["provider_used"] == "openai"
    assert report["summary"] == "Analise externa baseada no README publico."
    assert "FastAPI" in report["stack"]
    assert report["overall_score"] == cast(dict[str, Any], baseline_report)["overall_score"]
