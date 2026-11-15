"""Build the versioned before/after UX gallery from two capture folders.

The capture folders come from ``apps/web/tests/e2e/ux-baseline.spec.ts`` and ``ux-states.spec.ts``
(``CAPTURE_UX=1``, ``CAPTURE_UX_DIR``). They stay outside the repository; this script copies a
chosen subset into ``docs/assets/ux-comparison/<name>/`` as first-screen WebP crops (small enough
to version) and writes ``manifest.json`` with the SHA-256 of *every* capture file on each side, so
the full set can be regenerated and checked without being committed.

    python scripts/build_ux_gallery.py --before <dir> [--after <dir>] --out docs/assets/ux-comparison/2026-11-v5
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

# (gallery id, path inside the capture folder, crop height or None for the whole image)
SELECTION: list[tuple[str, str, int | None]] = [
    ("dashboard-desktop", "dashboard/desktop.png", 900),
    ("dashboard-desktop-dark", "dashboard/desktop-dark.png", 900),
    ("dashboard-mobile", "dashboard/mobile.png", 844),
    ("dashboard-tablet", "dashboard/tablet.png", 768),
    ("profile-desktop", "profile/desktop.png", 900),
    ("resume-studio-desktop", "resume-studio/desktop.png", 900),
    ("profile-desktop-dark", "profile/desktop-dark.png", 900),
    ("profile-mobile", "profile/mobile.png", 844),
    ("resume-studio-mobile", "resume-studio/mobile.png", 844),
    ("radar-desktop", "radar/desktop.png", 900),
    ("tracker-desktop", "tracker/desktop.png", 900),
    ("application-lab-desktop", "application-lab/desktop.png", 900),
    ("approvals-desktop", "approvals/desktop.png", 900),
    ("settings-mobile", "settings/mobile.png", 844),
    ("search-curriculo", "_states/search-currículo.png", None),
    ("navigation-mobile", "_states/navigation-mobile-open.png", None),
    ("api-unreachable", "_states/api-unreachable-dashboard.png", None),
    ("resume-studio-first-use", "_states/resume-studio-first-use.png", None),
    ("first-visit", "_states/first-visit-desktop.png", None),
]


def _digest(folder: Path) -> dict[str, str]:
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file() and path.suffix in {".png", ".json"}
    }


def _export(source: Path, target: Path, crop: int | None) -> None:
    with Image.open(source) as image:
        frame = image.convert("RGB")
        if crop is not None and frame.height > crop:
            frame = frame.crop((0, 0, frame.width, crop))
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.save(target, "WEBP", quality=82, method=6)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--before-sha", default="")
    parser.add_argument("--after-sha", default="")
    args = parser.parse_args()

    manifest: dict[str, object] = {
        "spec": [
            "apps/web/tests/e2e/ux-baseline.spec.ts",
            "apps/web/tests/e2e/ux-states.spec.ts",
        ],
        "browser": "Chromium (Playwright), deviceScaleFactor 1, prefers-reduced-motion: reduce",
        "data": "modo demo, dados fictícios do próprio frontend; estados com API simulada por page.route",
        "sides": {},
        "gallery": [],
    }
    sides = {"before": (args.before, args.before_sha)}
    if args.after:
        sides["after"] = (args.after, args.after_sha)
    for side, (folder, sha) in sides.items():
        manifest["sides"][side] = {"sha": sha, "files": _digest(folder)}  # type: ignore[index]
    for gallery_id, relative, crop in SELECTION:
        row: dict[str, object] = {"id": gallery_id, "source": relative, "crop_height": crop}
        for side, (folder, _sha) in sides.items():
            source = folder / relative
            if source.is_file():
                target = args.out / f"{gallery_id}-{side}.webp"
                _export(source, target, crop)
                row[side] = target.name
        manifest["gallery"].append(row)  # type: ignore[union-attr]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
