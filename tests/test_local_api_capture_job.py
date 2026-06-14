from modules.local_api import (
    BrowserCapturePayload,
    CompanionCaptureStore,
    LocalCompanionApp,
    LocalCompanionService,
)
from modules.memory import CareerMemory, MemoryStore
from modules.opportunities import OpportunityStore
from modules.storage.local_store import LocalStore
from modules.tracker.job_tracker import JobTracker


def _service(tmp_path):
    return LocalCompanionService(
        capture_store=CompanionCaptureStore(tmp_path / "captures.jsonl"),
        opportunity_store=OpportunityStore(tmp_path / "opportunities.json"),
        memory=CareerMemory(MemoryStore(tmp_path / "memory.jsonl")),
        tracker=JobTracker(LocalStore(tmp_path / "history.json")),
        context_path=tmp_path / "context.json",
    )


def test_local_api_capture_becomes_opportunity_and_memory(tmp_path):
    service = _service(tmp_path)
    app = LocalCompanionApp(service)
    capture = BrowserCapturePayload(
        page_title="Desenvolvedor Python Júnior",
        url="https://jobs.example/vaga-python",
        domain="jobs.example",
        job_title="Desenvolvedor Python Júnior",
        company="Example",
        description="Vaga remota para Python, FastAPI e SQL.",
    )

    status, payload = app.handle(
        "POST",
        "/capture/job",
        body=capture.model_dump_json().encode(),
    )

    assert status == 200
    assert payload["capture_id"]
    assert service.opportunity_store.list()[0].title == capture.job_title
    assert service.memory.store.list_memory_items(kind="opportunity")
