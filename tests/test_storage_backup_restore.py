from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile

import pytest
from modules.storage.backup import BackupFile, BackupManifest, create_backup, restore_backup
from modules.storage.database import connect_database
from modules.storage.health import check_data_health
from modules.storage.migrations import MigrationRunner


def test_backup_restore_excludes_secrets_and_validates_checksums(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "profile").mkdir(parents=True)
    (data_dir / "profile" / "profiles.json").write_text(
        json.dumps({"profiles": [{"profile_id": "default"}]}), encoding="utf-8"
    )
    (data_dir / "secrets").mkdir()
    (data_dir / "secrets" / "provider.json").write_text(
        json.dumps({"api_key": "material-que-nao-deve-sair"}), encoding="utf-8"
    )
    (data_dir / "accidental.json").write_text(
        json.dumps({"api_key": "material-longo-que-tambem-nao-deve-sair"}), encoding="utf-8"
    )
    MigrationRunner(data_dir / "sotuhire.db").apply(create_backup=False)

    backup = create_backup(data_dir=data_dir, destination=tmp_path / "backup.zip")
    with zipfile.ZipFile(backup.archive_path) as bundle:
        names = set(bundle.namelist())
        assert "profile/profiles.json" in names
        assert "sotuhire.db" in names
        assert "accidental.json" not in names
        assert not any("secret" in name.casefold() for name in names)
        assert "material-que-nao-deve-sair" not in "".join(
            bundle.read(name).decode("utf-8", errors="ignore") for name in names
        )
        assert "accidental.json" in backup.manifest.excluded_files

    dry_run = restore_backup(backup.archive_path, destination=tmp_path / "restore", dry_run=True)
    assert dry_run.files_validated == 2
    assert dry_run.files_restored == 0

    restored = restore_backup(backup.archive_path, destination=tmp_path / "restore", dry_run=False)
    assert restored.files_restored == 2
    assert (tmp_path / "restore" / "sotuhire.db").exists()
    assert (tmp_path / "restore" / "profile" / "profiles.json").exists()


def test_restore_rejects_tampered_archive(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "state.json").write_text('{"id":"one"}', encoding="utf-8")
    backup = create_backup(data_dir=data_dir, destination=tmp_path / "backup.zip")
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(backup.archive_path) as source, zipfile.ZipFile(tampered, "w") as target:
        for name in source.namelist():
            payload = b'{"id":"two"}' if name == "state.json" else source.read(name)
            target.writestr(name, payload)

    with pytest.raises(ValueError, match="Checksum"):
        restore_backup(tampered, destination=tmp_path / "restore", dry_run=True)


def test_restore_rejects_corrupt_sqlite_even_with_matching_checksum(tmp_path):
    payload = b"not-a-sqlite-database"
    manifest = BackupManifest(
        schema_version=3,
        files=[
            BackupFile(
                path="sotuhire.db",
                size=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
            )
        ],
    )
    archive = tmp_path / "corrupt.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("sotuhire.db", payload)
        bundle.writestr("manifest.json", manifest.model_dump_json())

    with pytest.raises(ValueError, match="SQLite"):
        restore_backup(archive, destination=tmp_path / "restore", dry_run=True)


def test_backup_manifest_reports_actual_schema_version(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    legacy_only = create_backup(data_dir=data_dir, destination=tmp_path / "legacy.zip")
    assert legacy_only.manifest.schema_version == 0
    assert legacy_only.manifest.max_supported_schema_version == 3

    MigrationRunner(data_dir / "sotuhire.db").apply(create_backup=False)
    migrated = create_backup(data_dir=data_dir, destination=tmp_path / "migrated.zip")
    assert migrated.manifest.schema_version == 3


def test_data_health_reports_schema_and_corrupt_legacy_json(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sotuhire-history.json").write_text("{invalid", encoding="utf-8")
    MigrationRunner(data_dir / "sotuhire.db").apply(create_backup=False)

    report = check_data_health(data_dir=data_dir)

    assert report.schema_version == 3
    assert not report.healthy
    assert any(item.code == "legacy_json_corrupt" for item in report.issues)


def test_data_health_detects_invalid_dates_and_missing_snapshots(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    MigrationRunner(data_dir / "sotuhire.db").apply(create_backup=False)
    with connect_database(data_dir / "sotuhire.db") as connection:
        connection.execute(
            """INSERT INTO opportunities
            (id, payload, source_ref, content_hash, created_at, updated_at)
            VALUES ('job-1', '{}', 'https://example.test/job', 'hash', 'not-a-date', '2026-01-01')"""
        )

    report = check_data_health(data_dir=data_dir)

    assert report.healthy
    assert any(item.code == "invalid_date" for item in report.issues)
    assert any(item.code == "opportunity_snapshot_missing" for item in report.issues)


def test_data_health_does_not_mutate_a_pre_schema_database(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    database = data_dir / "sotuhire.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE legacy_only (id TEXT PRIMARY KEY)")
    before = database.read_bytes()

    report = check_data_health(data_dir=data_dir)

    assert not report.healthy
    assert report.schema_version == 0
    assert database.read_bytes() == before
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert tables == {"legacy_only"}


def test_data_health_reports_schema_metadata_divergence(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    database = data_dir / "sotuhire.db"
    MigrationRunner(database).apply(create_backup=False)
    with connect_database(database) as connection:
        connection.execute("UPDATE schema_metadata SET value = '2' WHERE key = 'schema_version'")

    report = check_data_health(data_dir=data_dir)

    assert not report.healthy
    assert any(
        item.code == "database_validation_failed" and "Schema divergente" in item.message
        for item in report.issues
    )


def test_data_health_reports_unreadable_database_instead_of_raising(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sotuhire.db").write_bytes(b"not-a-sqlite-database")

    report = check_data_health(data_dir=data_dir)

    assert not report.healthy
    assert any(item.code == "database_unreadable" for item in report.issues)
