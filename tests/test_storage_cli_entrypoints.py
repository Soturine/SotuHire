import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_data_cli_entrypoints_run_from_outside_repository(tmp_path):
    for name in (
        "backup_data.py",
        "restore_data.py",
        "check_data_health.py",
        "migrate_local_data.py",
    ):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / name), "--help"],
            cwd=tmp_path,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout


def test_migration_cli_dry_run_does_not_create_database(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "migrate_local_data.py"),
            "--dry-run",
            "--data-dir",
            str(data_dir),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert '"mode": "dry-run"' in result.stdout
    assert not (data_dir / "sotuhire.db").exists()
