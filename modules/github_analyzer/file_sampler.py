"""Select repository files for content-aware GitHub analysis."""

from __future__ import annotations

from pathlib import PurePosixPath

from modules.github_analyzer.file_filters import (
    is_content_sampleable_entry,
    language_hint_for_path,
    normalize_repo_path,
)
from modules.github_analyzer.repository_models import (
    RepositoryTree,
    RepositoryTreeEntry,
    SelectedRepositoryFile,
)

PRIORITY_NAMES = {
    ".env.example",
    "build.gradle",
    "cargo.toml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "dockerfile",
    "go.mod",
    "mkdocs.yml",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "readme.md",
    "requirements-dev.txt",
    "requirements.txt",
}

PRIORITY_PREFIXES = (
    ".github/workflows/",
    "app/",
    "docs/",
    "modules/",
    "src/",
    "tests/",
)

ENTRYPOINT_NAMES = {
    "app.py",
    "main.py",
    "manage.py",
    "server.py",
    "index.js",
    "main.js",
    "app.js",
    "index.ts",
    "main.ts",
    "app.ts",
}


def select_repository_files(
    tree: RepositoryTree,
    *,
    central_files: list[str] | None = None,
    max_files: int = 40,
    max_file_chars: int = 12_000,
    max_total_chars: int = 120_000,
) -> list[SelectedRepositoryFile]:
    """Select a bounded, explainable set of files for raw-content fetching."""
    central = {normalize_repo_path(path).casefold() for path in central_files or []}
    candidates = [entry for entry in tree.entries if is_content_sampleable_entry(entry)]
    ranked = sorted(candidates, key=lambda entry: _rank_key(entry, central))
    selected: list[SelectedRepositoryFile] = []
    total_budget = 0
    for entry in ranked:
        if len(selected) >= max_files:
            break
        expected_chars = min(entry.size or max_file_chars, max_file_chars)
        if total_budget + expected_chars > max_total_chars and selected:
            continue
        selected.append(
            SelectedRepositoryFile(
                path=normalize_repo_path(entry.path),
                reason_selected=_selection_reason(entry, central),
                size=entry.size,
                language_hint=language_hint_for_path(entry.path),
            )
        )
        total_budget += expected_chars
    return selected


def _rank_key(entry: RepositoryTreeEntry, central: set[str]) -> tuple[int, int, str]:
    path = normalize_repo_path(entry.path)
    lower = path.casefold()
    name = PurePosixPath(lower).name
    if lower in central:
        priority = 0
    elif name in PRIORITY_NAMES:
        priority = 1
    elif lower.startswith(".github/workflows/"):
        priority = 2
    elif name in ENTRYPOINT_NAMES:
        priority = 3
    elif lower.startswith(("src/", "modules/", "app/")):
        priority = 4
    elif lower.startswith("tests/") or "/tests/" in lower:
        priority = 5
    elif lower.startswith("docs/"):
        priority = 6
    else:
        priority = 9
    return (priority, path.count("/"), path)


def _selection_reason(entry: RepositoryTreeEntry, central: set[str]) -> str:
    path = normalize_repo_path(entry.path)
    lower = path.casefold()
    name = PurePosixPath(lower).name
    if lower in central:
        return "dependency_central"
    if name.startswith("readme"):
        return "readme"
    if name in PRIORITY_NAMES:
        return "config"
    if lower.startswith(".github/workflows/"):
        return "workflow"
    if lower.startswith("tests/") or "/tests/" in lower or name.startswith("test_"):
        return "test"
    if lower.startswith("docs/"):
        return "docs"
    if lower.startswith(("src/", "modules/", "app/")) or name in ENTRYPOINT_NAMES:
        return "source"
    return "sample"
