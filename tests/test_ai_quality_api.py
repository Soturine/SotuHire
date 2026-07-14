from apps.api.main import create_app
from fastapi.testclient import TestClient
from modules.ai.benchmark_store import AiBenchmark, AiBenchmarkStore
from modules.ai.feedback import AiFeedbackStore
from modules.storage.ai_runs import AiRun, AiRunStore
from modules.storage.migrations import MigrationRunner


def test_ai_quality_feedback_and_run_endpoints(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    database = tmp_path / "sotuhire.db"
    MigrationRunner(database).apply(create_backup=False)
    run = AiRunStore(database).save(
        AiRun(
            task_id="ats_review",
            feature="ats",
            prompt_id="ats_analysis_v1",
            prompt_version="1.0.0",
            latency_ms=25,
            schema_valid=True,
        )
    )
    client = TestClient(create_app())

    summary = client.get("/api/v1/ai/quality/summary")
    runs = client.get("/api/v1/ai/quality/runs?limit=1")
    feedback = client.post(
        "/api/v1/ai/feedback",
        json={
            "run_id": run.run_id,
            "task_id": "ats_review",
            "rating": "useful",
            "decision": "accepted",
        },
    )

    assert summary.status_code == 200
    assert summary.json()["data"]["executions"] == 1
    assert runs.json()["data"]["items"][0]["run_id"] == run.run_id
    assert feedback.status_code == 200
    feedback_id = feedback.json()["data"]["feedback_id"]
    assert client.get("/api/v1/ai/feedback").json()["data"]["items"]
    assert client.delete(f"/api/v1/ai/feedback/{feedback_id}").status_code == 200
    assert AiFeedbackStore(database).list() == []


def test_ai_quality_reads_the_dedicated_sanitized_benchmark_store(tmp_path, monkeypatch) -> None:
    benchmark_database = tmp_path / "benchmarks.db"
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path / "personal"))
    monkeypatch.setenv("SOTUHIRE_BENCHMARK_DATABASE", str(benchmark_database))
    AiBenchmarkStore(benchmark_database).save_run(
        AiBenchmark(
            app_version="1.9.7",
            suite="golden",
            providers=["local"],
            seed=197,
            dataset_version="v1.9.7-1",
            environment="local",
            status="completed",
        )
    )

    response = TestClient(create_app()).get("/api/v1/ai/quality/benchmarks")

    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["providers"] == ["local"]
