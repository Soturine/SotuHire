from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_ROOTS = [
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "apps" / "web" / "src",
    ROOT / "apps" / "web" / "public",
    ROOT / "apps" / "web" / "index.html",
    ROOT / "apps" / "web" / "README.md",
    ROOT / "apps" / "api",
    ROOT / "docs",
    ROOT / "scripts" / "README.md",
    ROOT / "browser-extension" / "README.md",
]
SUFFIXES = {".html", ".md", ".json", ".ts", ".tsx", ".js", ".py"}
IGNORED_PARTS = {"node_modules", "dist", "site", "__pycache__", ".git"}
MOJIBAKE_PATTERNS = [
    re.compile(r"\u00c3[\u0080-\u00bf\u0160\u0161\u2018-\u201d\u2020-\u2022]"),
    re.compile(r"\u00c2"),
    re.compile(r"\u00e2\u20ac"),
]


def _iter_public_text_files() -> list[Path]:
    files: list[Path] = []
    for root in TEXT_ROOTS:
        if not root.exists():
            continue
        if root.is_file():
            files.append(root)
            continue
        files.extend(
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUFFIXES
            and not set(path.parts) & IGNORED_PARTS
            and "docs/assets/screenshots" not in path.as_posix()
        )
    return files


def test_public_text_files_do_not_contain_common_mojibake() -> None:
    offenders: list[str] = []
    for path in _iter_public_text_files():
        text = path.read_text(encoding="utf-8")
        found = [pattern.pattern for pattern in MOJIBAKE_PATTERNS if pattern.search(text)]
        if found:
            offenders.append(f"{path.relative_to(ROOT)}: {', '.join(found)}")

    assert offenders == []
