"""Keep the test process isolated from a developer's local-first data.

Every variable that tells the app where to write is forced to a folder of this run, overriding
whatever the shell or a `.env` says (`app.py` loads `.env` without overriding what is already set).
A session guard then fails the run if anything under the checkout's own `data/` or `benchmarks/`
changed: those are where a cwd-relative default would land (SH-NEW-040).
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TEST_DATA_DIR = _ROOT / ".pytest_cache" / "isolated-data" / uuid4().hex

# Forced, never setdefault: a SOTUHIRE_DATA_DIR exported for daily use must not receive test writes.
os.environ["SOTUHIRE_DATA_DIR"] = str(_TEST_DATA_DIR)
os.environ["SOTUHIRE_BENCHMARK_DATABASE"] = str(_TEST_DATA_DIR / "benchmarks" / "ai-quality.db")

_GUARDED = ("data", "benchmarks")


def _snapshot() -> dict[str, tuple[int, int]]:
    """Size and mtime of every file under the guarded folders (metadata only, nothing is read)."""
    files: dict[str, tuple[int, int]] = {}
    for name in _GUARDED:
        folder = _ROOT / name
        if not folder.is_dir():
            continue
        for path in folder.rglob("*"):
            try:
                if not path.is_file():
                    continue
                stat = path.stat()
            except OSError:  # vanished or locked while walking (a SQLite -journal)
                continue
            files[path.relative_to(_ROOT).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return files


def pytest_sessionstart(session: pytest.Session) -> None:
    session.config.stash[_SNAPSHOT_KEY] = _snapshot()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    before = session.config.stash.get(_SNAPSHOT_KEY, None)
    if before is None:
        return
    after = _snapshot()
    changed = sorted(
        path for path in before.keys() | after.keys() if before.get(path) != after.get(path)
    )
    if changed:
        listing = "\n  ".join(changed[:20])
        session.config.get_terminal_writer().line(
            f"\nTest isolation broken: the run changed the checkout's own data:\n  {listing}",
            red=True,
        )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


_SNAPSHOT_KEY = pytest.StashKey[dict]()
