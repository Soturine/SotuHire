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


def test_local_api_capture_public_exam_does_not_become_private_job(tmp_path):
    service = _service(tmp_path)
    app = LocalCompanionApp(service)
    capture = BrowserCapturePayload(
        kind="public_exam",
        page_title="Edital 01/2026",
        url="https://banca.example/editais/01-2026",
        domain="banca.example",
        visible_text="Edital 01/2026\nCargo: Analista\nInscricoes: 01/08/2026 a 20/08/2026.",
        description="Edital 01/2026\nCargo: Analista\nInscricoes: 01/08/2026 a 20/08/2026.",
    )

    status, payload = app.handle(
        "POST",
        "/capture/public-exam",
        body=capture.model_dump_json().encode(),
    )
    context_status, context_payload = app.handle("GET", "/capture/context-summary")

    assert status == 200
    assert payload["capture_id"]
    record = service.capture_store.get(str(payload["capture_id"]))
    assert record is not None
    assert record.capture.kind == "public_exam"
    assert service.opportunity_store.list() == []
    assert context_status == 200
    assert isinstance(context_payload, dict)
    enabled_flows = context_payload.get("enabled_flows")
    assert isinstance(enabled_flows, list)
    assert "public_exam" in enabled_flows
