"""Verify SotuHire from an exported, untracked-artifact-free checkout."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--install",
        action="store_true",
        help="Create a fresh venv and install .[dev] before validating.",
    )
    parser.add_argument(
        "--skip-e2e",
        action="store_true",
        help="Skip the Chromium smoke suite; useful when browsers are unavailable.",
    )
    args = parser.parse_args()

    _require("git")
    _require("node")
    _require("npm.cmd" if os.name == "nt" else "npm")
    with tempfile.TemporaryDirectory(prefix="sotuhire-clean-") as temporary:
        checkout = Path(temporary) / "SotuHire"
        checkout.mkdir()
        archive = Path(temporary) / "source.tar"
        with archive.open("wb") as target:
            subprocess.run(
                ["git", "archive", "--format=tar", "HEAD"],
                cwd=ROOT,
                stdout=target,
                check=True,
            )
        with tarfile.open(archive) as package:
            package.extractall(checkout)

        python = Path(sys.executable)
        if args.install:
            venv = checkout / ".venv"
            _run([str(python), "-m", "venv", str(venv)], checkout)
            python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            _run([str(python), "-m", "pip", "install", "-e", ".[dev]"], checkout)

        _run([str(python), "-m", "compileall", "modules", "tests", "apps", "scripts"], checkout)
        _run([str(python), "-m", "pytest", "-q"], checkout)
        _run([str(python), "scripts/package_extension.py"], checkout)
        _run([str(python), "-m", "mkdocs", "build", "--strict"], checkout)

        web = checkout / "apps" / "web"
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm") or "npm"
        _run([npm, "ci"], web)
        _run([npm, "run", "lint"], web)
        _run([npm, "run", "typecheck"], web)
        _run([npm, "run", "build"], web)
        if not args.skip_e2e:
            env = {**os.environ, "SOTUHIRE_E2E_PORT": "57325"}
            _run([npm, "run", "test:e2e", "--", "--project=chromium"], web, env=env)

        print(f"Clean install verified from commit archive: {checkout}")


def _require(command: str) -> None:
    if shutil.which(command) is None:
        raise RuntimeError(f"Required command not found: {command}")


def _run(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
) -> None:
    print(f"[{cwd.name}] {' '.join(command)}")
    subprocess.run(command, cwd=cwd, env=env, check=True)


if __name__ == "__main__":
    main()
