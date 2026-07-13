import pytest
from modules.storage.ai_runs import AiRun, AiRunStore


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

    store.save(run)
    restored = store.list(feature="match")

    assert restored == [run]
    assert restored[0].fallback_used is True
    assert restored[0].provider_requested == "openai"


def test_ai_run_store_rejects_secret_like_values(tmp_path):
    store = AiRunStore(tmp_path / "sotuhire.db")
    synthetic_secret = "s" + "k-" + ("x" * 24)

    with pytest.raises(ValueError, match="segredo"):
        store.save(AiRun(feature="match", warnings=[synthetic_secret]))
