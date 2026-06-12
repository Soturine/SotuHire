"""Parser placeholder for LinkedIn official CSV exports."""

from __future__ import annotations

from pathlib import Path


def discover_linkedin_csv_files(export_dir: str | Path) -> list[Path]:
    """Return CSV files from an extracted LinkedIn export directory."""
    base = Path(export_dir)
    if not base.exists():
        return []
    return sorted(base.rglob("*.csv"))
