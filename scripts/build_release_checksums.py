"""Write deterministic SHA-256 checksums for the current release assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def default_assets() -> tuple[Path, ...]:
    """Asset names derived from the versioned manifests, never hardcoded per release."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = json.loads(
        (ROOT / "browser-extension" / "manifest.json").read_text(encoding="utf-8")
    )
    return (
        DIST / f"sotuhire-extension-v{manifest['version']}.zip",
        DIST / f"sotuhire-sbom-v{project['project']['version']}.cdx.json",
    )


DEFAULT_ASSETS = default_assets()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", type=Path, nargs="*", default=DEFAULT_ASSETS)
    parser.add_argument("--output", type=Path, default=DIST / "SHA256SUMS")
    args = parser.parse_args()

    missing = [path for path in args.assets if not path.is_file()]
    if missing:
        parser.error(f"release asset missing: {', '.join(map(str, missing))}")

    lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in sorted(args.assets, key=lambda item: item.name.casefold())
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"SHA-256 checksums written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
