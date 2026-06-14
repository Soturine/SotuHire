from pathlib import Path

from modules.local_api import LocalCompanionApp, LocalCompanionService
from modules.memory import CareerMemory, MemoryStore
from modules.portfolio import (
    ProjectAnalysisPayload,
    ProjectAnalysisStore,
    analyze_project,
    enhance_project_report,
)


def test_extension_exposes_standalone_and_connected_project_modes():
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    html = Path("browser-extension/popup.html").read_text(encoding="utf-8")

    assert "SotuHireProjectAnalyzer.analyze" in popup
    assert "/capture/repo-analysis" in popup
    assert "Analisar projeto no navegador" in html
    assert "Salvar projeto no SotuHire" in html


def test_connected_project_analysis_saves_memory(tmp_path):
    service = LocalCompanionService(
        memory=CareerMemory(MemoryStore(tmp_path / "memory.jsonl")),
        project_store=ProjectAnalysisStore(tmp_path / "projects.jsonl"),
    )
    app = LocalCompanionApp(service)
    body = b'{"url":"https://github.example/example/repo","page_type":"github_repo","title":"Repo","languages":["Python"]}'

    status, payload = app.handle("POST", "/capture/github-repo", body=body)

    assert status == 200
    assert payload["report"]["github_profile_score"] >= 0
    assert service.project_store.list()
    assert service.memory.store.list_memory_items(kind="project_evidence")


def test_connected_gemini_project_analysis_has_local_fallback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    payload = ProjectAnalysisPayload(
        url="https://github.example/example/repo",
        page_type="github_repo",
        provider_used="gemini",
        languages=["Python"],
    )
    local = analyze_project(payload.model_copy(update={"provider_used": "local"}))

    enhanced = enhance_project_report(payload, local)

    assert enhanced.provider_used == "local"
    assert enhanced.overall_score == local.overall_score
