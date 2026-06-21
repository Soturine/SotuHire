"""Path filtering rules for repository tree and content sampling."""

from __future__ import annotations

from pathlib import PurePosixPath

from modules.github_analyzer.repository_models import RepositoryTreeEntry

IGNORED_TREE_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "site",
    "venv",
}

IGNORED_CONTENT_NAMES = {
    "package-lock.json",
    "pipfile.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "yarn.lock",
}

BINARY_SUFFIXES = {
    ".7z",
    ".avi",
    ".bin",
    ".bmp",
    ".dll",
    ".doc",
    ".docx",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".lock",
    ".mov",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".rar",
    ".svg",
    ".tar",
    ".webm",
    ".webp",
    ".zip",
}

TEXT_SUFFIX_LANGUAGE_HINTS = {
    ".cs": "C#",
    ".css": "CSS",
    ".go": "Go",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".jsx": "React",
    ".kt": "Kotlin",
    ".md": "Markdown",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".sh": "Shell",
    ".sql": "SQL",
    ".swift": "Swift",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "React",
    ".txt": "Text",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
}

DEFAULT_MAX_CONTENT_BYTES = 200_000


def normalize_repo_path(path: str) -> str:
    """Normalize a repository path to a stable POSIX-like form."""
    return path.replace("\\", "/").strip("/")


def is_tree_visible_path(path: str) -> bool:
    """Return whether a path should appear in the prompt tree."""
    normalized = normalize_repo_path(path).casefold()
    if not normalized:
        return False
    parts = set(normalized.split("/"))
    return not bool(parts & IGNORED_TREE_PARTS)


def is_binary_path(path: str) -> bool:
    """Return whether a path is unsafe or useless for text sampling."""
    suffix = PurePosixPath(normalize_repo_path(path).casefold()).suffix
    return suffix in BINARY_SUFFIXES


def is_content_sampleable_path(path: str, *, size_bytes: int | None = None) -> bool:
    """Return whether file content can be included in analysis context."""
    normalized = normalize_repo_path(path)
    lower = normalized.casefold()
    name = PurePosixPath(lower).name
    return not (
        not is_tree_visible_path(normalized)
        or is_binary_path(normalized)
        or name in IGNORED_CONTENT_NAMES
        or (size_bytes is not None and size_bytes > DEFAULT_MAX_CONTENT_BYTES)
    )


def is_content_sampleable_entry(entry: RepositoryTreeEntry) -> bool:
    """Return whether a tree entry can be sampled as text."""
    return entry.type == "blob" and is_content_sampleable_path(
        entry.path,
        size_bytes=entry.size,
    )


def language_hint_for_path(path: str) -> str:
    """Infer a lightweight language hint from a repository path."""
    normalized = normalize_repo_path(path)
    lower = normalized.casefold()
    name = PurePosixPath(lower).name
    if name == "dockerfile":
        return "Dockerfile"
    if name in {"makefile", "justfile"}:
        return "Build script"
    return TEXT_SUFFIX_LANGUAGE_HINTS.get(PurePosixPath(lower).suffix, "")
