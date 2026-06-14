from modules.local_api import (
    BrowserCapturePayload,
    CaptureActionRequest,
    CompanionAnalysisContext,
    CompanionCaptureStore,
    LocalCompanionService,
)
from modules.memory import CareerMemory, MemoryStore
from modules.opportunities import OpportunityStore
from modules.storage.local_store import LocalStore
from modules.tracker.job_tracker import JobTracker


def test_extension_capture_creates_one_stable_opportunity_memory(tmp_path):
    memory = CareerMemory(MemoryStore(tmp_path / "memory.jsonl"))
    service = LocalCompanionService(
        capture_store=CompanionCaptureStore(tmp_path / "captures.jsonl"),
        opportunity_store=OpportunityStore(tmp_path / "opportunities.json"),
        memory=memory,
        tracker=JobTracker(LocalStore(tmp_path / "history.json")),
        context_path=tmp_path / "context.json",
    )
    capture = BrowserCapturePayload(
        page_title="Pessoa Desenvolvedora Python",
        job_title="Pessoa Desenvolvedora Python",
        company="Example Tech",
        url="https://jobs.example/123?tracking=first",
        description="Vaga para Python, SQL e APIs.",
    )

    first = service.capture_job(capture)
    second = service.capture_job(
        capture.model_copy(update={"url": "https://jobs.example/123?tracking=second"})
    )

    assert first.capture_id == second.capture_id
    assert len(service.capture_store.list()) == 1
    assert len(memory.store.list_memory_items(kind="opportunity")) == 1


def test_extension_capture_can_be_analyzed_and_sent_to_tracker_memory(tmp_path):
    memory_path = tmp_path / "memory" / "career-memory.jsonl"
    memory = CareerMemory(MemoryStore(memory_path))
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    service = LocalCompanionService(
        capture_store=CompanionCaptureStore(tmp_path / "captures.jsonl"),
        opportunity_store=OpportunityStore(tmp_path / "opportunities.json"),
        memory=memory,
        tracker=tracker,
        context_path=tmp_path / "context.json",
    )
    service.save_active_context(
        CompanionAnalysisContext(
            resume_text="Pessoa desenvolvedora com Python, SQL e APIs.",
            provider="local",
        )
    )
    captured = service.capture_job(
        BrowserCapturePayload(
            page_title="Pessoa Desenvolvedora Python",
            job_title="Pessoa Desenvolvedora Python",
            company="Example Tech",
            url="https://jobs.example/456",
            description="Vaga para Python, SQL e APIs.",
        )
    )

    analyzed = service.analyze_capture(CaptureActionRequest(capture_id=captured.capture_id))
    tracked = service.track_capture(CaptureActionRequest(capture_id=captured.capture_id))

    assert analyzed.match_score is not None
    assert tracked.tracker_id
    assert len(tracker.list_analyses()) == 1
    kinds = {item.kind for item in memory.store.list_memory_items()}
    assert {"opportunity", "job_analysis", "tracker_event"} <= kinds
