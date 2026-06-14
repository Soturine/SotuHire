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

    assert status == 200
    assert payload["saved_to_memory"] is True
    assert payload["report"]["overall_score"] > 0
    assert service.project_store.list()
    assert memory.store.list_memory_items(kind="project_evidence")
