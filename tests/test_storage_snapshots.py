from __future__ import annotations

import pytest
from modules.storage import (
    AiRun,
    AiRunStore,
    AnalysisSnapshot,
    ApplicationRecord,
    ApplicationRepository,
    JobSnapshot,
    ResumeSnapshot,
    SnapshotStore,
)


def test_snapshots_are_content_addressed_and_application_keeps_links(tmp_path):
    database = tmp_path / "sotuhire.db"
    snapshots = SnapshotStore(database)
    first_job = snapshots.create_job(
        JobSnapshot(
            opportunity_id="job-1",
            title="Analista",
            organization="Organização",
            raw_text="Descrição original",
            source_url="https://example.com/jobs/1",
        )
    )
    same_job = snapshots.create_job(
        JobSnapshot(
            opportunity_id="job-1",
            title="Analista",
            organization="Organização",
            raw_text="Descrição original",
            source_url="https://example.com/jobs/1",
        )
    )
    changed_job = snapshots.create_job(
        JobSnapshot(
            opportunity_id="job-1",
            title="Analista",
            organization="Organização",
            raw_text="Descrição atualizada",
            source_url="https://example.com/jobs/1",
        )
    )
    resume = snapshots.create_resume(
        ResumeSnapshot(profile_id="default", content="Currículo realmente usado")
    )
    analysis = snapshots.create_analysis(
        AnalysisSnapshot(
            analysis_type="match",
            job_snapshot_id=first_job.snapshot_id,
            resume_snapshot_id=resume.snapshot_id,
            result={"match_score": 82},
            evidence_used=["Python"],
        )
    )

    assert same_job.snapshot_id == first_job.snapshot_id
    assert changed_job.snapshot_id != first_job.snapshot_id
    assert changed_job.content_hash != first_job.content_hash

    applications = ApplicationRepository(database)
    saved = applications.save(
        ApplicationRecord(
            id="application-1",
            job_snapshot_id=first_job.snapshot_id,
            resume_snapshot_id=resume.snapshot_id,
            match_analysis_snapshot_id=analysis.snapshot_id,
            job_title="Analista",
            organization="Organização",
        )
    )
    loaded = applications.get(saved.id)
    assert loaded is not None
    assert loaded.job_snapshot_id == first_job.snapshot_id
    loaded_job = snapshots.get_job(first_job.snapshot_id)
    assert loaded_job is not None
    assert loaded_job.raw_text == "Descrição original"


def test_ai_run_store_rejects_secret_shaped_metadata(tmp_path):
    store = AiRunStore(tmp_path / "sotuhire.db")
    run = store.save(
        AiRun(
            feature="match",
            provider_requested="openai",
            provider_used="local",
            fallback_used=True,
            analysis_mode="fallback",
            fallback_reason="Provider indisponível.",
            input_hash="safe-hash",
        )
    )
    assert store.list(feature="match")[0].run_id == run.run_id

    with pytest.raises(ValueError, match="segredo"):
        store.save(AiRun(feature="match", warnings=["authorization: material privado"]))
