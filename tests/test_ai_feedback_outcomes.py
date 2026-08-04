from datetime import UTC, datetime, timedelta

import pytest
from modules.ai.feedback import AiFeedback, AiFeedbackStore
from modules.outcomes import OutcomeEvent, OutcomeStore
from modules.storage.ai_runs import AiRun, AiRunStore
from modules.storage.applications import ApplicationRecord, ApplicationRepository
from modules.storage.migrations import MigrationRunner


def test_feedback_can_be_created_listed_and_deleted(tmp_path) -> None:
    database = tmp_path / "sotuhire.db"
    MigrationRunner(database).apply(create_backup=False)
    run = AiRunStore(database).save(
        AiRun(task_id="resume_tailor", feature="tailor", prompt_id="resume_tailor_v1")
    )
    store = AiFeedbackStore(database)
    feedback = store.save(
        AiFeedback(
            run_id=run.run_id,
            task_id="resume_tailor",
            rating="partial",
            decision="edited",
            edited=True,
            unsupported_claim=True,
            comment="Ajustei uma frase sem evidência.",
        )
    )

    assert store.list(run_id=run.run_id) == [feedback]
    assert store.delete(feedback.feedback_id) is True
    assert store.list(run_id=run.run_id) == []


def test_outcomes_show_small_sample_and_non_causal_signals(tmp_path) -> None:
    database = tmp_path / "sotuhire.db"
    MigrationRunner(database).apply(create_backup=False)
    application = ApplicationRepository(database).save(
        ApplicationRecord(id="application-1", job_title="Vaga fictícia")
    )
    store = OutcomeStore(database)
    started = datetime(2026, 1, 1, tzinfo=UTC)
    store.save(
        OutcomeEvent(
            application_id=application.id,
            event_type="application_submitted_manually",
            occurred_at=started,
            source="Fonte fictícia",
            resume_variant_id="variant-a",
            match_score=80,
            ats_score=75,
        )
    )
    store.save(
        OutcomeEvent(
            application_id=application.id,
            event_type="response_received",
            occurred_at=started + timedelta(hours=48),
            source="Fonte fictícia",
            resume_variant_id="variant-a",
        )
    )

    summary = store.summary()

    assert summary.sample_size == 1
    assert summary.confidence == "insufficient"
    assert summary.response_rate.value == 1
    assert summary.average_time_to_response_hours == 48
    assert "causalidade" in summary.note
    assert "Amostra pequena" in summary.response_rate.note


def test_outcome_denominator_uses_only_manual_submissions_and_keeps_no_reply(tmp_path) -> None:
    database = tmp_path / "sotuhire.db"
    draft = ApplicationRepository(database).save(ApplicationRecord(id="draft"))
    submitted = ApplicationRepository(database).save(ApplicationRecord(id="submitted"))
    store = OutcomeStore(database, no_response_window_days=7)
    started = datetime(2026, 1, 1, tzinfo=UTC)
    store.save(
        OutcomeEvent(
            application_id=draft.id,
            event_type="application_created",
            occurred_at=started,
        )
    )
    store.save(
        OutcomeEvent(
            application_id=submitted.id,
            event_type="application_submitted_manually",
            occurred_at=started,
        )
    )

    summary = store.summary()

    assert summary.sample_size == 1
    assert summary.response_rate.denominator == 1
    assert summary.response_rate.numerator == 0

    with pytest.raises(ValueError, match="7 dias"):
        store.save(
            OutcomeEvent(
                application_id=submitted.id,
                event_type="no_response",
                occurred_at=started + timedelta(days=6),
            )
        )

    store.save(
        OutcomeEvent(
            application_id=submitted.id,
            event_type="no_response",
            occurred_at=started + timedelta(days=8),
        )
    )
    assert store.summary().response_rate.denominator == 1
