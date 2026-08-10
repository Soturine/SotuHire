"""Scan repository paths for provider-key patterns without printing secret values."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PATTERNS = (
    re.compile(rb"(?<![0-9A-Za-z_-])AIza[0-9A-Za-z_-]{20,}"),
    re.compile(rb"(?<![0-9A-Za-z_-])sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
)
EXCLUDED_PARTS = {
    ".git",
    ".tmp",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
}
EXCLUDED_PREFIXES = (".tmp-",)
MAX_BYTES = 10 * 1024 * 1024


def candidate_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
            continue
        if path.is_dir():
            files.extend(
                item for item in path.rglob("*") if item.is_file() and not _is_excluded(item)
            )
    return sorted(set(files))


def _is_excluded(path: Path) -> bool:
    return bool(EXCLUDED_PARTS.intersection(path.parts)) or any(
        part.startswith(EXCLUDED_PREFIXES) for part in path.parts
    )


def has_secret_pattern(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_BYTES:
            return False
        content = path.read_bytes()
    except OSError:
        return False
    if _content_has_secret(content):
        return True
    if path.suffix.casefold() != ".zip":
        return False
    try:
        with ZipFile(path) as archive:
            for member in archive.infolist():
                if member.is_dir() or member.file_size > MAX_BYTES:
                    continue
                if _content_has_secret(archive.read(member)):
                    return True
    except (BadZipFile, OSError, RuntimeError):
        return False
    return False


def _content_has_secret(content: bytes) -> bool:
    from modules.security.credentials import contains_provider_secret

    if any(pattern.search(content) for pattern in PATTERNS):
        return True
    text = content.decode("utf-8", errors="ignore")
    return contains_provider_secret(text, require_context_for_modern_gemini=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", nargs="+", type=Path, default=[Path(".")])
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Print affected file paths only; matched values are always withheld.",
    )
    args = parser.parse_args()
    files = candidate_files(args.paths)
    affected = [path for path in files if has_secret_pattern(path)]
    if affected:
        print(
            f"Secret scan failed: provider-key pattern found in {len(affected)} file(s); "
            "values withheld."
        )
        if args.show_paths:
            for path in affected:
                print(f"Affected path: {path}")
        return 1
    print(f"Secret scan passed: {len(files)} file(s), no provider-key pattern found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
