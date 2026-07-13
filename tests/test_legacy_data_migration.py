from __future__ import annotations

import json

from modules.storage.database import connect_database
from modules.storage.legacy_migration import migrate_local_data
from modules.storage.snapshots import SnapshotStore


def test_dry_run_is_read_only_and_apply_preserves_ids_counts_and_sources(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "profile").mkdir(parents=True)
    (data_dir / "memory").mkdir(parents=True)
    profile_path = data_dir / "profile" / "profiles.json"
    profile_path.write_text(
        json.dumps(
            {
                "active_profile_id": "default",
                "profiles": [
                    {
                        "profile_id": "default",
                        "items": [
                            {
                                "item_id": "skill-1",
                                "title": "Python",
                                "source_ref": "resume:item:1",
                                "confirmed_by_user": True,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    memory_path = data_dir / "memory" / "career-memory.jsonl"
    memory_path.write_text(
        json.dumps(
            {
                "id": "memory-1",
                "kind": "skill",
                "title": "Python",
                "source": "resume",
                "source_id": "resume:item:1",
            }
        )
        + "\n{invalid-line\n",
        encoding="utf-8",
    )
    tracker_path = data_dir / "sotuhire-history.json"
    tracker_path.write_text(
        json.dumps(
            [
                {
                    "id": "application-1",
                    "job_title": "Analista",
                    "company": "Organização",
                    "status": "applied",
                }
            ]
        ),
        encoding="utf-8",
    )
    original_profile = profile_path.read_bytes()
    original_memory = memory_path.read_bytes()

    dry_run = migrate_local_data(mode="dry-run", data_dir=data_dir)
    assert dry_run.found["profiles"] == 1
    assert dry_run.found["profile_items"] == 1
    assert dry_run.rejected["memory/career-memory.jsonl"] == 1
    assert not (data_dir / "sotuhire.db").exists()
    assert not (data_dir / "backups").exists()

    applied = migrate_local_data(mode="apply", data_dir=data_dir)
    assert not applied.success  # a linha corrompida foi explicitamente rejeitada
    assert applied.backup_path is not None and applied.backup_path.exists()
    assert applied.imported["profiles"] == 1
    assert applied.imported["profile_items"] == 1
    assert applied.imported["memories"] == 1
    assert applied.imported["applications"] == 1
    assert profile_path.read_bytes() == original_profile
    assert memory_path.read_bytes() == original_memory

    with connect_database(data_dir / "sotuhire.db") as connection:
        assert connection.execute("SELECT id FROM profiles").fetchone()[0] == "default"
        assert connection.execute("SELECT id FROM profile_items").fetchone()[0] == "skill-1"
        assert connection.execute("SELECT id FROM memories").fetchone()[0] == "memory-1"
        application = connection.execute("SELECT id, job_snapshot_id FROM applications").fetchone()
        assert tuple(application) == ("application-1", None)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    repeated = migrate_local_data(mode="apply", data_dir=data_dir)
    assert repeated.imported == {}
    assert sum(repeated.duplicates.values()) >= 4


def test_migration_creates_job_snapshot_when_original_text_exists(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "companion").mkdir(parents=True)
    capture = {
        "id": "capture-1",
        "capture": {
            "kind": "job",
            "url": "https://example.com/jobs/1",
            "job_title": "Pessoa Analista",
            "company": "Exemplo",
            "visible_text": "Descrição original completa da vaga",
        },
    }
    (data_dir / "companion" / "captures.jsonl").write_text(
        json.dumps(capture) + "\n", encoding="utf-8"
    )

    report = migrate_local_data(mode="apply", data_dir=data_dir)

    assert report.success
    assert report.imported["captures"] == 1
    assert report.imported["job_snapshots"] == 1
    with connect_database(data_dir / "sotuhire.db") as connection:
        snapshot = connection.execute("SELECT raw_text, source_url FROM job_snapshots").fetchone()
        assert tuple(snapshot) == (
            "Descrição original completa da vaga",
            "https://example.com/jobs/1",
        )


def test_dry_run_rejects_scalar_json_without_creating_database(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sotuhire-history.json").write_text("42", encoding="utf-8")

    report = migrate_local_data(mode="dry-run", data_dir=data_dir)

    assert report.rejected == {"sotuhire-history.json": 1}
    assert not report.success
    assert not (data_dir / "sotuhire.db").exists()


def test_migration_deduplicates_strong_urls_and_exact_memory_preserving_ids(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "memory").mkdir(parents=True)
    memories = [
        {
            "id": "memory-a",
            "kind": "skill",
            "title": "Python",
            "content": "API com FastAPI",
            "source": "resume",
            "source_id": "resume:a",
        },
        {
            "id": "memory-b",
            "kind": "skill",
            "title": "Python",
            "content": "API com FastAPI",
            "source": "github",
            "source_id": "repo:b",
        },
    ]
    (data_dir / "memory" / "career-memory.jsonl").write_text(
        "\n".join(json.dumps(item) for item in memories) + "\n", encoding="utf-8"
    )
    opportunities = [
        {
            "id": "job-a",
            "title": "Analista",
            "company": "Exemplo",
            "source_url": "https://example.test/jobs/1?utm_source=a",
            "description": "Descrição original",
        },
        {
            "id": "job-b",
            "title": "Analista",
            "company": "Exemplo",
            "source_url": "https://example.test/jobs/1?utm_source=b",
            "description": "Descrição original",
        },
    ]
    (data_dir / "sotuhire-opportunities.json").write_text(
        json.dumps(opportunities), encoding="utf-8"
    )

    dry_run = migrate_local_data(mode="dry-run", data_dir=data_dir)
    applied = migrate_local_data(mode="apply", data_dir=data_dir)

    assert dry_run.found["memories"] == 2
    assert dry_run.duplicates["memories"] == 1
    assert dry_run.duplicates["opportunities"] == 1
    assert applied.imported["memories"] == 1
    assert applied.imported["opportunities"] == 1
    assert applied.imported["job_snapshots"] == 1
    with connect_database(data_dir / "sotuhire.db") as connection:
        memory = json.loads(connection.execute("SELECT payload FROM memories").fetchone()[0])
        opportunity = json.loads(
            connection.execute("SELECT payload FROM opportunities").fetchone()[0]
        )
    assert memory["merged_legacy_ids"] == ["memory-a", "memory-b"]
    assert opportunity["merged_legacy_ids"] == ["job-a", "job-b"]


def test_migration_normalizes_public_exam_timeline_for_snapshot_readback(tmp_path):
    data_dir = tmp_path / "data"
    notices_dir = data_dir / "public_exams"
    notices_dir.mkdir(parents=True)
    notices_dir.joinpath("notices.json").write_text(
        json.dumps(
            {
                "notices": [
                    {
                        "notice_id": "notice-1",
                        "title": "Edital de exemplo",
                        "raw_text": "Texto oficial preservado",
                        "timeline": {"exam_date": "2026-10-01"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = migrate_local_data(mode="apply", data_dir=data_dir)

    assert report.success
    with connect_database(data_dir / "sotuhire.db") as connection:
        snapshot_id = connection.execute(
            "SELECT snapshot_id FROM public_exam_snapshots"
        ).fetchone()[0]
    snapshot = SnapshotStore(data_dir / "sotuhire.db").get_public_exam(snapshot_id)
    assert snapshot is not None
    assert snapshot.timeline == [{"exam_date": "2026-10-01"}]
