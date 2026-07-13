from __future__ import annotations

import zipfile
from pathlib import Path

from tests.api_test_helpers import api_client


def test_data_health_is_read_only_and_hides_absolute_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    legacy = tmp_path / "profile" / "profiles.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"profiles": [{"id": "profile-1"}]}', encoding="utf-8")
    before = legacy.read_bytes()

    response = api_client().get("/api/v1/data/health")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["healthy"] is True
    assert data["database_present"] is False
    assert data["schema_version"] == 0
    assert data["counts"]["legacy:profile/profiles.json"] == 1
    assert str(tmp_path) not in response.text
    assert legacy.read_bytes() == before
    assert not (tmp_path / "sotuhire.db").exists()


def test_data_reliability_is_advertised_and_present_in_openapi() -> None:
    client = api_client()

    health = client.get("/api/v1/health")
    paths = client.get("/openapi.json").json()["paths"]

    assert "data_reliability" in health.json()["data"]["capabilities"]
    assert "/api/v1/data/health" in paths
    assert "/api/v1/data/backups" in paths
    assert "/api/v1/data/backups/{archive_name}" in paths
    assert "/api/v1/data/restore" in paths


def test_backup_export_list_and_download_are_confined_to_managed_directory(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    source = tmp_path / "profile" / "profiles.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"profiles": [{"id": "profile-1"}]}', encoding="utf-8")
    client = api_client()

    backup_response = client.post("/api/v1/data/backups", json={"kind": "backup"})
    export_response = client.post("/api/v1/data/backups", json={"kind": "export"})

    assert backup_response.status_code == 200
    assert export_response.status_code == 200
    backup = backup_response.json()["data"]
    export = export_response.json()["data"]
    assert backup["kind"] == "backup"
    assert export["kind"] == "export"
    assert "archive_path" not in backup
    assert str(tmp_path) not in backup_response.text
    assert (tmp_path / "backups" / backup["archive_name"]).is_file()

    listed = client.get("/api/v1/data/backups")
    assert listed.status_code == 200
    names = {item["archive_name"] for item in listed.json()["data"]["archives"]}
    assert {backup["archive_name"], export["archive_name"]} <= names

    downloaded = client.get(backup["download_url"])
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "application/zip"
    assert downloaded.headers["cache-control"] == "no-store"
    downloaded_path = tmp_path / "downloaded.zip"
    downloaded_path.write_bytes(downloaded.content)
    with zipfile.ZipFile(downloaded_path) as bundle:
        assert "manifest.json" in bundle.namelist()
        assert "profile/profiles.json" in bundle.namelist()


def test_restore_validates_first_and_requires_exact_confirmation(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    source = tmp_path / "profile" / "profiles.json"
    source.parent.mkdir(parents=True)
    original = '{"profiles": [{"id": "original"}]}'
    source.write_text(original, encoding="utf-8")
    client = api_client()
    created = client.post("/api/v1/data/backups", json={"kind": "backup"}).json()["data"]
    archive_name = created["archive_name"]
    source.write_text('{"profiles": [{"id": "changed"}]}', encoding="utf-8")

    dry_run = client.post("/api/v1/data/restore", json={"archive_name": archive_name})

    assert dry_run.status_code == 200
    dry_data = dry_run.json()["data"]
    assert dry_data["dry_run"] is True
    assert dry_data["files_validated"] == 1
    assert dry_data["files_restored"] == 0
    assert "changed" in source.read_text(encoding="utf-8")

    unconfirmed = client.post(
        "/api/v1/data/restore",
        json={"archive_name": archive_name, "apply": True, "confirmation": "sim"},
    )
    assert unconfirmed.status_code == 400
    assert "RESTAURAR" in unconfirmed.json()["error"]["message"]
    assert "changed" in source.read_text(encoding="utf-8")

    restored = client.post(
        "/api/v1/data/restore",
        json={"archive_name": archive_name, "apply": True, "confirmation": "RESTAURAR"},
    )
    assert restored.status_code == 200
    restore_data = restored.json()["data"]
    assert restore_data["dry_run"] is False
    assert restore_data["files_restored"] == 1
    assert restore_data["pre_restore_backup_name"].startswith("sotuhire-data-backup-")
    assert source.read_text(encoding="utf-8") == original


def test_restore_rejects_paths_and_unknown_archives(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    traversal = client.post(
        "/api/v1/data/restore",
        json={"archive_name": "../sotuhire-data-backup-test.zip"},
    )
    missing = client.post(
        "/api/v1/data/restore",
        json={"archive_name": "sotuhire-data-backup-missing.zip"},
    )

    assert traversal.status_code == 422
    assert missing.status_code == 404
    assert str(tmp_path) not in missing.text


def test_data_health_reports_corrupt_database_without_leaking_path(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    (tmp_path / "sotuhire.db").write_bytes(b"not-a-sqlite-database")

    response = api_client().get("/api/v1/data/health")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["healthy"] is False
    assert any(item["code"] == "database_unreadable" for item in data["issues"])
    assert str(tmp_path) not in response.text
