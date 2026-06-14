from pathlib import Path

from scripts import capture_screenshots


def test_screenshot_capture_restores_local_state(tmp_path: Path, monkeypatch):
    existing = tmp_path / "memory.jsonl"
    created_during_capture = tmp_path / "profile.json"
    existing.write_bytes(b"original")
    monkeypatch.setattr(
        capture_screenshots,
        "LOCAL_STATE_PATHS",
        (existing, created_during_capture),
    )

    snapshot = capture_screenshots._snapshot_local_state()
    existing.write_bytes(b"fixture")
    created_during_capture.write_bytes(b"fixture")
    capture_screenshots._restore_local_state(snapshot)

    assert existing.read_bytes() == b"original"
    assert not created_during_capture.exists()
