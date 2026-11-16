"""C09: backup → change everything → restore → the same data, read through the API; and rollback.

The existing restore test covers one JSON file. This one uses the stores a person actually fills:
the Universal Profile, the Master Resume and its variants (SQLite), the Tracker and the Career
Copilot evidence graph. After the restore the API must answer exactly as before the changes; the
automatic pre-restore backup must bring the changed state back (rollback of the restore itself).
"""

from __future__ import annotations

from pathlib import Path

from modules.profile.models import ProfileItem
from modules.profile.service import UniversalCareerProfileService
from tests.api_test_helpers import api_client

STUDIO = "/api/v1/resume-studio"


def _state(client) -> dict:
    profile = client.get("/api/v1/profile").json()["data"]["profile"]
    master = client.get(f"{STUDIO}/master").json()["data"]["resume"]
    variants = client.get(
        f"{STUDIO}/variants", params={"master_resume_id": master["master_resume_id"]}
    )
    jobs = client.get("/api/v1/tracker/jobs").json()["data"]["jobs"]
    evidence = client.get("/api/v2/evidence").json()["data"]
    return {
        "profile_items": sorted(item["title"] for item in profile["items"]),
        "headline": profile.get("headline"),
        "master_titles": sorted(
            entry["title"] for section in master["sections"] for entry in section["entries"]
        ),
        "variant_titles": sorted(v["title"] for v in variants.json()["data"]["items"]),
        "jobs": sorted((job["job_title"], job["status"]) for job in jobs),
        "evidence": sorted(node["title"] for node in evidence),
    }


def _restore(client, archive: str) -> dict:
    response = client.post(
        "/api/v1/data/restore",
        json={"archive_name": archive, "apply": True, "confirmation": "RESTAURAR"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_backup_restore_round_trip_and_rollback(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    profile = UniversalCareerProfileService()
    profile.add_item(ProfileItem(type="experience", title="Enfermeira assistencial"))
    client.put("/api/v1/profile", json={"headline": "Enfermeira UTI"})
    master = client.post(f"{STUDIO}/master/from-profile", json={}).json()["data"]["resume"]
    variant = {
        "resume_variant_id": "variant-round-trip",
        "master_resume_id": master["master_resume_id"],
        "title": "Variante hospital A",
        "target_role": "Enfermeira",
        "sections": master["sections"],
    }
    assert client.post(f"{STUDIO}/variants", json={"variant": variant}).status_code == 200
    assert client.post(
        "/api/v1/tracker/jobs", json={"title": "Enfermeira UTI", "company": "H"}
    ).status_code in (200, 201)
    client.post("/api/v2/evidence", json={"node_type": "certification", "title": "COREN ativo"})
    saved = _state(client)

    archive = client.post("/api/v1/data/backups", json={"kind": "backup"}).json()["data"][
        "archive_name"
    ]

    # change every store after the backup
    profile.add_item(ProfileItem(type="language", title="Inglês"))
    client.put("/api/v1/profile", json={"headline": "Outra headline"})
    client.patch(f"{STUDIO}/variants/variant-round-trip", json={"title": "Renomeada"})
    job_id = client.get("/api/v1/tracker/jobs").json()["data"]["jobs"][0]["id"]
    client.patch(f"/api/v1/tracker/jobs/{job_id}", json={"status": "applied"})
    client.post("/api/v2/evidence", json={"node_type": "project", "title": "Projeto novo"})
    changed = _state(client)
    assert changed != saved

    result = _restore(client, archive)

    assert _state(client) == saved
    # the restore kept its own way back: restoring the automatic pre-restore backup is a rollback
    _restore(client, result["pre_restore_backup_name"])
    assert _state(client) == changed


def test_backups_in_the_same_second_never_overwrite_each_other(tmp_path: Path) -> None:
    """Archive names had one-second resolution and were opened with "w": the second backup of a
    second replaced the first. A restore takes a safety backup first, so restoring a backup made a
    moment earlier destroyed it (the restore failed with "Arquivo ZIP inválido")."""
    import zipfile

    from modules.storage.backup import create_backup

    (tmp_path / "profile").mkdir()
    (tmp_path / "profile" / "profiles.json").write_text('{"v": 1}', encoding="utf-8")
    first = create_backup(data_dir=tmp_path).archive_path
    (tmp_path / "profile" / "profiles.json").write_text('{"v": 2}', encoding="utf-8")
    second = create_backup(data_dir=tmp_path).archive_path
    third = create_backup(data_dir=tmp_path).archive_path

    assert len({first, second, third}) == 3
    with zipfile.ZipFile(first) as bundle:
        assert bundle.read("profile/profiles.json") == b'{"v": 1}'
