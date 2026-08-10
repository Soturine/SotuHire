from __future__ import annotations

import pytest
from modules.local_api import CompanionCaptureStore
from modules.profile import UniversalCareerProfileStore
from modules.profile.models import UniversalCareerProfile, UniversalCareerProfileState
from modules.storage.health import check_data_health
from modules.storage.json_recovery import (
    JsonStoreCorruptionError,
    JsonStoreWriteBlockedError,
    json_store_health,
    restore_json_store,
)
from modules.storage.safe_paths import UnsafeStorePath


def test_profile_corruption_is_quarantined_blocked_and_explicitly_restored(tmp_path) -> None:
    path = tmp_path / "profile" / "profiles.json"
    store = UniversalCareerProfileStore(path)
    first = UniversalCareerProfileState(
        profiles=[UniversalCareerProfile(profile_id="default", display_name="Pessoa Fictícia")]
    )
    store.save_state(first)
    store.save_state(first)
    backup = next((path.parent / ".backups").glob("*.bak"))
    path.write_text("{corrompido", encoding="utf-8")

    with pytest.raises(JsonStoreCorruptionError) as raised:
        store.load_state()

    assert raised.value.quarantine_path is not None
    assert raised.value.quarantine_path.read_text(encoding="utf-8") == "{corrompido"
    assert json_store_health(path).status == "degraded"
    report = check_data_health(data_dir=tmp_path)
    assert any(issue.code == "json_store_degraded" for issue in report.issues)
    with pytest.raises(JsonStoreWriteBlockedError):
        store.save_state(first)

    restore_json_store(path, backup)

    assert json_store_health(path).status == "healthy"
    assert store.load_active().display_name == "Pessoa Fictícia"


def test_companion_jsonl_corruption_never_returns_false_empty_state(tmp_path) -> None:
    path = tmp_path / "captures.jsonl"
    path.write_text('{"id":"incompleto"}\n{invalid', encoding="utf-8")
    store = CompanionCaptureStore(path)

    with pytest.raises(JsonStoreCorruptionError):
        store.list()

    assert json_store_health(path).status == "degraded"
    assert list((tmp_path / ".quarantine").glob("captures.jsonl.*.corrupt"))


def test_restore_rejects_external_and_arbitrary_sources(tmp_path) -> None:
    root = tmp_path / "store-root"
    target = root / "profiles.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")
    external = tmp_path / "external.json"
    external.write_text("{}", encoding="utf-8")

    with pytest.raises(UnsafeStorePath):
        restore_json_store(target, external, store_root=root)

    arbitrary_inside = root / "arbitrary.json"
    arbitrary_inside.write_text("{}", encoding="utf-8")
    with pytest.raises(UnsafeStorePath):
        restore_json_store(target, arbitrary_inside, store_root=root)
