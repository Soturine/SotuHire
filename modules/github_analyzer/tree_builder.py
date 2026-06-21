"""Build readable repository trees and repository-level signals."""

from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from modules.github_analyzer.file_filters import is_tree_visible_path, normalize_repo_path
from modules.github_analyzer.repository_models import (
    RepositoryDetectedSignals,
    RepositoryTree,
    RepositoryTreeEntry,
)

README_NAMES = {"readme", "readme.md", "readme.rst", "readme.txt"}
MANIFEST_NAMES = {
    "build.gradle",
    "cargo.toml",
    "composer.json",
    "go.mod",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements.txt",
    "setup.py",
}
LOCK_NAMES = {"package-lock.json", "pipfile.lock", "pnpm-lock.yaml", "poetry.lock", "yarn.lock"}
LICENSE_NAMES = {"license", "license.md", "license.txt"}
SECURITY_NAMES = {
    "codeowners",
    "dependabot.yml",
    "dependabot.yaml",
    "security.md",
    "security.txt",
}
ENV_EXAMPLES = {".env.example", ".env.sample", "env.example"}
DOCKER_NAMES = {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}


def visible_tree_entries(tree: RepositoryTree) -> list[RepositoryTreeEntry]:
    """Return stable tree entries after removing generated repository noise."""
    return sorted(
        [entry for entry in tree.entries if is_tree_visible_path(entry.path)],
        key=lambda entry: (entry.path.count("/"), entry.path.casefold()),
    )


def build_directory_tree(
    tree: RepositoryTree,
    *,
    max_entries: int = 500,
    max_depth: int = 6,
) -> str:
    """Build a compact textual directory tree for prompts and reports."""
    lines = ["."]
    included = 0
    children: dict[str, set[str]] = defaultdict(set)
    file_nodes: set[str] = set()
    for entry in visible_tree_entries(tree):
        normalized = normalize_repo_path(entry.path)
        if not normalized:
            continue
        parts = normalized.split("/")
        if len(parts) > max_depth:
            parts = [*parts[:max_depth], "..."]
        current = ""
        for part in parts:
            parent = current
            current = f"{current}/{part}" if current else part
            children[parent].add(current)
        if entry.type == "blob":
            file_nodes.add(current)

    def walk(parent: str, prefix: str = "") -> None:
        nonlocal included
        nodes = sorted(children.get(parent, set()), key=lambda item: (item not in file_nodes, item))
        for index, node in enumerate(nodes):
            if included >= max_entries:
                return
            connector = "`-- " if index == len(nodes) - 1 else "|-- "
            name = PurePosixPath(node).name
            marker = _importance_marker(node)
            lines.append(f"{prefix}{connector}{name}{marker}")
            included += 1
            if node not in file_nodes:
                extension = "    " if index == len(nodes) - 1 else "|   "
                walk(node, prefix + extension)

    walk("")
    if included >= max_entries:
        lines.append(f"... tree limited to {max_entries} entries")
    if tree.truncated:
        lines.append("... GitHub reported this tree as truncated")
    return "\n".join(lines)


def detect_repository_signals(tree: RepositoryTree) -> RepositoryDetectedSignals:
    """Detect repository capabilities from tree presence, not file content."""
    test_paths: list[str] = []
    doc_paths: list[str] = []
    workflow_paths: list[str] = []
    manifest_paths: list[str] = []
    security_paths: list[str] = []
    skipped_paths: list[str] = []
    has_readme = False
    has_docker = False
    has_env_example = False
    has_dependency_lock = False
    has_large_files_skipped = False

    for entry in tree.entries:
        normalized = normalize_repo_path(entry.path)
        lower = normalized.casefold()
        name = PurePosixPath(lower).name
        parts = lower.split("/")
        if not is_tree_visible_path(normalized):
            skipped_paths.append(normalized)
            continue
        if entry.size is not None and entry.size > 200_000:
            has_large_files_skipped = True
        if name in README_NAMES:
            has_readme = True
            doc_paths.append(normalized)
        if name in MANIFEST_NAMES:
            manifest_paths.append(normalized)
        if name in LOCK_NAMES:
            has_dependency_lock = True
        if name in LICENSE_NAMES:
            doc_paths.append(normalized)
        if name in SECURITY_NAMES or lower.startswith(".github/dependabot"):
            security_paths.append(normalized)
        if name in ENV_EXAMPLES:
            has_env_example = True
            security_paths.append(normalized)
        if name in DOCKER_NAMES:
            has_docker = True
            manifest_paths.append(normalized)
        if (
            "tests" in parts
            or "test" in parts
            or name.startswith("test_")
            or name.endswith(".test.ts")
        ):
            test_paths.append(normalized)
        if "docs" in parts or name in README_NAMES:
            doc_paths.append(normalized)
        if lower.startswith(".github/workflows/") and lower.endswith((".yml", ".yaml")):
            workflow_paths.append(normalized)

    return RepositoryDetectedSignals(
        has_readme=has_readme,
        has_tests=bool(test_paths),
        has_ci=bool(workflow_paths),
        has_docker=has_docker,
        has_docs=bool(doc_paths),
        has_license=any(PurePosixPath(path.casefold()).name in LICENSE_NAMES for path in doc_paths),
        has_env_example=has_env_example,
        has_package_manifest=bool(manifest_paths),
        has_security_policy=bool(security_paths),
        has_dependency_lock=has_dependency_lock,
        has_large_files_skipped=has_large_files_skipped,
        tree_truncated=tree.truncated,
        test_paths=sorted(set(test_paths)),
        doc_paths=sorted(set(doc_paths)),
        workflow_paths=sorted(set(workflow_paths)),
        manifest_paths=sorted(set(manifest_paths)),
        security_paths=sorted(set(security_paths)),
        skipped_paths=sorted(set(skipped_paths))[:100],
    )


def _importance_marker(path: str) -> str:
    lower = path.casefold()
    name = PurePosixPath(lower).name
    if name in README_NAMES:
        return " [README]"
    if lower.startswith(".github/workflows/"):
        return " [CI]"
    if "tests/" in f"{lower}/" or name.startswith("test_"):
        return " [TEST]"
    if name in MANIFEST_NAMES:
        return " [MANIFEST]"
    if name in DOCKER_NAMES:
        return " [DOCKER]"
    return ""
