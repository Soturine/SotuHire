from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from modules.storage.applications import ApplicationRecord, ApplicationRepository
from modules.storage.database import connect_database
from modules.storage.migrations import ensure_database


def _session(database) -> None:
    ensure_database(database)
    with connect_database(database) as connection:
        connection.execute(
            """INSERT INTO application_lab_sessions
            (session_id, job_id, status, created_at, updated_at)
            VALUES ('session-transaction', 'job-fixture', 'review', ?, ?)""",
            ("2026-08-03T00:00:00+00:00", "2026-08-03T00:00:00+00:00"),
        )


def test_lab_unit_of_work_rolls_back_card_outcome_session_and_key(tmp_path) -> None:
    database = tmp_path / "sotuhire.db"
    _session(database)
    repository = ApplicationRepository(database)

    with pytest.raises(Exception, match="FOREIGN KEY"):
        repository.complete_lab_transaction(
            ApplicationRecord(id="application-failing", job_snapshot_id="missing-snapshot"),
            session_id="session-transaction",
            idempotency_key="failing-operation",
        )

    with connect_database(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM applications").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM outcome_events").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM idempotency_records").fetchone()[0] == 0
        session = connection.execute(
            "SELECT status, tracker_application_id FROM application_lab_sessions"
        ).fetchone()
        assert tuple(session) == ("review", None)


def test_lab_unit_of_work_is_idempotent_under_concurrency(tmp_path) -> None:
    database = tmp_path / "sotuhire.db"
    _session(database)
    record = ApplicationRecord(
        id="application-stable",
        job_title="Vaga fictícia",
        payload={"application_lab": {"match_score": 70, "ats_score": 65}},
    )

    def complete() -> str:
        return (
            ApplicationRepository(database)
            .complete_lab_transaction(
                record,
                session_id="session-transaction",
                idempotency_key="stable-operation-key",
            )
            .id
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: complete(), range(2)))

    assert results == ["application-stable", "application-stable"]
    with connect_database(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM applications").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM outcome_events").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM idempotency_records").fetchone()[0] == 1
        session = connection.execute(
            "SELECT status, tracker_application_id FROM application_lab_sessions"
        ).fetchone()
        assert tuple(session) == ("completed", "application-stable")


def test_missing_capture_is_a_pending_link_without_placeholder(tmp_path) -> None:
    database = tmp_path / "sotuhire.db"
    repository = ApplicationRepository(database)

    saved = repository.save(
        ApplicationRecord(id="application-pending", source_capture_id="external-capture")
    )

    assert saved.source_capture_id == ""
    assert saved.source_capture_external_reference == "external-capture"
    assert saved.link_state == "pending_link"
    with connect_database(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM captures").fetchone()[0] == 0
