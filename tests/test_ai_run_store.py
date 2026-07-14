from datetime import UTC, datetime, timedelta

import pytest
from modules.storage.ai_runs import AiRun, AiRunStore, AiTraceSettings


def test_ai_run_store_round_trips_auditable_metadata(tmp_path):
    store = AiRunStore(tmp_path / "sotuhire.db")
    run = AiRun(
        feature="match",
        provider_requested="openai",
        provider_used="local",
        model_requested="example-model",
        fallback_used=True,
        fallback_reason="provider indisponível",
        prompt_id="match_analysis_evidence_based_v1",
        prompt_version="1.0.0",
        analysis_mode="fallback",
        input_hash="hash-seguro",
        source_refs=["profile:item-1"],
        warnings=["Resultado requer revisão."],
    )

    saved = store.save(run)
    restored = store.list(feature="match")

    assert restored == [saved]
    assert restored[0].fallback_used is True
    assert restored[0].provider_requested == "openai"


def test_ai_run_store_sanitizes_secret_like_error_values(tmp_path):
    store = AiRunStore(tmp_path / "sotuhire.db")
    synthetic_secret = "s" + "k-" + ("x" * 24)

    saved = store.save(AiRun(feature="match", warnings=[synthetic_secret]))

    assert synthetic_secret not in saved.model_dump_json()
    assert "REDACTED" in saved.model_dump_json()


def test_ai_run_store_rejects_secret_in_identity_metadata(tmp_path):
    store = AiRunStore(tmp_path / "sotuhire.db")
    synthetic_secret = "s" + "k-" + ("x" * 24)

    with pytest.raises(ValueError, match="segredo"):
        store.save(AiRun(feature="match", model_requested=synthetic_secret))


def test_ai_run_store_supports_complete_metadata_pagination_and_retention(tmp_path):
    settings = AiTraceSettings(ai_trace_retention_days=30)
    store = AiRunStore(tmp_path / "sotuhire.db", settings=settings)
    now = datetime.now(UTC)
    old = store.save(
        AiRun(
            task_id="match_explanation",
            feature="match",
            context_purpose="match",
            context_source_types=["profile", "memory"],
            context_item_count=3,
            evidence_count=2,
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
            benchmark_run_id="benchmark-1",
            parent_run_id="parent-1",
            started_at=now - timedelta(days=45),
            finished_at=now - timedelta(days=45),
            created_at=now - timedelta(days=45),
        )
    )
    current = store.save(AiRun(task_id="ats_review", feature="ats"))

    assert store.list(limit=1, offset=0) == [current]
    assert store.list(limit=1, offset=1) == [old]
    assert store.get(old.run_id) == old
    assert store.purge_expired(now=now) == 1
    assert store.count() == 1
