"""File sampling rules for repository analysis."""

from __future__ import annotations

PRIORITY_NAMES = {
    "readme.md",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "dockerfile",
    "docker-compose.yml",
    "mkdocs.yml",
}


def prioritize_paths(paths: list[str], limit: int = 25) -> list[str]:
    """Prioritize files that best explain a repository."""

    def key(path: str) -> tuple[int, str]:
        lower = path.lower().split("/")[-1]
        priority = (
            0
            if lower in PRIORITY_NAMES or path.startswith(("docs/", "tests/", ".github/workflows/"))
            else 1
        )
        return (priority, path)

    return sorted(paths, key=key)[:limit]
