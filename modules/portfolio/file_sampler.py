"""File sampling rules for repository analysis."""

from __future__ import annotations

PRIORITY_NAMES = {
    "readme.md",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "mkdocs.yml",
    "license",
    "license.md",
    "contributing.md",
}
PRIORITY_PREFIXES = ("src/", "app/", "modules/", "docs/", "tests/", ".github/workflows/")
IGNORED_PARTS = {
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "coverage",
}
IGNORED_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".exe",
    ".dll",
    ".bin",
    ".lock",
}


def prioritize_paths(paths: list[str], limit: int = 25) -> list[str]:
    """Prioritize files that best explain a repository."""

    def key(path: str) -> tuple[int, str]:
        normalized = path.replace("\\", "/").strip("/")
        lower = normalized.lower().split("/")[-1]
        priority = (
            0
            if lower in PRIORITY_NAMES
            else 1
            if normalized.lower().startswith(PRIORITY_PREFIXES)
            else 2
        )
        return (priority, normalized)

    eligible = [path.replace("\\", "/").strip("/") for path in paths if is_sampleable_path(path)]
    return list(dict.fromkeys(sorted(eligible, key=key)))[:limit]


def is_sampleable_path(path: str, *, size_bytes: int | None = None) -> bool:
    """Return whether a repository path is useful and safe to sample."""
    normalized = path.replace("\\", "/").strip("/").lower()
    parts = set(normalized.split("/"))
    suffix = "." + normalized.rsplit(".", 1)[-1] if "." in normalized.rsplit("/", 1)[-1] else ""
    return not (
        parts & IGNORED_PARTS
        or suffix in IGNORED_SUFFIXES
        or (size_bytes is not None and size_bytes > 200_000)
    )
