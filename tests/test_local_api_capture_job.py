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

TOKEN = "companion-test-token"


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
    app = LocalCompanionApp(service, token=TOKEN)
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
        token=TOKEN,
    )

    assert status == 200
    assert payload["capture_id"]
    assert service.opportunity_store.list()[0].title == capture.job_title
    assert service.memory.store.list_memory_items(kind="opportunity")


def test_local_api_capture_public_exam_does_not_become_private_job(tmp_path):
    service = _service(tmp_path)
    app = LocalCompanionApp(service, token=TOKEN)
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
        token=TOKEN,
    )
    context_status, context_payload = app.handle("GET", "/capture/context-summary", token=TOKEN)

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


def test_recapturing_an_unchanged_page_is_not_a_changed_job(tmp_path):
    """Found driving the extension in Chromium (Companion mode): every capture of the same page
    answered "A vaga mudou" because the capture's own timestamp was part of the hashed snapshot."""
    from datetime import UTC, datetime, timedelta

    app = LocalCompanionApp(_service(tmp_path), token=TOKEN)
    first_at = datetime(2026, 11, 15, 10, 0, tzinfo=UTC)
    answers = []
    for captured_at in (first_at, first_at + timedelta(minutes=5)):
        capture = BrowserCapturePayload(
            page_title="Desenvolvedor Python Júnior",
            url="https://jobs.example/vaga-python",
            domain="jobs.example",
            job_title="Desenvolvedor Python Júnior",
            company="Example",
            description="Vaga remota para Python, FastAPI e SQL.",
            captured_at=captured_at,
        )
        status, payload = app.handle(
            "POST", "/capture/job", body=capture.model_dump_json().encode(), token=TOKEN
        )
        assert status == 200
        answers.append(payload)

    assert answers[1]["capture_id"] == answers[0]["capture_id"]
    assert answers[1]["snapshot_id"] == answers[0]["snapshot_id"]
    assert answers[1].get("artifact_status") != "stale"


def test_a_real_change_is_still_reported_as_changed(tmp_path):
    app = LocalCompanionApp(_service(tmp_path), token=TOKEN)
    answers = []
    for description in ("Vaga remota para Python.", "Vaga presencial para Python e Go."):
        capture = BrowserCapturePayload(
            page_title="Desenvolvedor Python Júnior",
            url="https://jobs.example/vaga-python",
            domain="jobs.example",
            job_title="Desenvolvedor Python Júnior",
            company="Example",
            description=description,
        )
        _, payload = app.handle(
            "POST", "/capture/job", body=capture.model_dump_json().encode(), token=TOKEN
        )
        answers.append(payload)
    assert answers[1]["snapshot_id"] != answers[0]["snapshot_id"]
    assert answers[1]["artifact_status"] == "stale"
