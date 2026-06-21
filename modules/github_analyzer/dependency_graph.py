"""Heuristic dependency graph extraction for sampled repository files."""

from __future__ import annotations

import re
from collections import Counter

from pydantic import Field

from modules.github_analyzer.file_filters import normalize_repo_path
from modules.github_analyzer.repository_models import (
    RepositoryAnalyzerModel,
    SelectedRepositoryFile,
)

PYTHON_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([A-Za-z_][\w.]*)\s+import\s+|import\s+([A-Za-z_][\w.]*))",
    re.MULTILINE,
)
JS_IMPORT_RE = re.compile(
    r"(?:from\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))"
)


class DependencyGraphSummary(RepositoryAnalyzerModel):
    """Small dependency graph summary used to improve file sampling."""

    central_files: list[str] = Field(default_factory=list)
    import_edges: list[tuple[str, str]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def build_dependency_graph(files: list[SelectedRepositoryFile]) -> DependencyGraphSummary:
    """Extract lightweight import edges from selected file contents."""
    edges: list[tuple[str, str]] = []
    unresolved: list[str] = []
    known_paths = {
        normalize_repo_path(file.path).casefold(): normalize_repo_path(file.path) for file in files
    }
    for file in files:
        source = normalize_repo_path(file.path)
        if not file.content.strip():
            continue
        imports = _extract_imports(source, file.content)
        for imported in imports:
            target = _resolve_import(source, imported, known_paths)
            edges.append((source, target or imported))
            if not target:
                unresolved.append(imported)

    central_files = _central_files(edges)
    notes = []
    if unresolved:
        notes.append(f"{len(unresolved)} imports could not be mapped to sampled files.")
    if not edges:
        notes.append("No import edges detected in sampled files.")
    return DependencyGraphSummary(
        central_files=central_files,
        import_edges=edges[:300],
        notes=notes,
    )


def _extract_imports(path: str, content: str) -> list[str]:
    lower = path.casefold()
    if lower.endswith(".py"):
        output: list[str] = []
        for match in PYTHON_IMPORT_RE.finditer(content):
            module = match.group(1) or match.group(2) or ""
            if module:
                output.append(module.split(",")[0].strip())
        return output
    if lower.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
        return [
            imported
            for match in JS_IMPORT_RE.finditer(content)
            for imported in match.groups()
            if imported
        ]
    return []


def _resolve_import(
    source: str,
    imported: str,
    known_paths: dict[str, str],
) -> str:
    if imported.startswith("."):
        base_parts = source.split("/")[:-1]
        import_parts = [part for part in imported.split("/") if part and part != "."]
        while import_parts and import_parts[0] == "..":
            if base_parts:
                base_parts.pop()
            import_parts.pop(0)
        candidates = ["/".join([*base_parts, *import_parts]).casefold()]
    else:
        dotted = imported.replace(".", "/")
        candidates = [dotted.casefold()]
    suffixes = ["", ".py", ".js", ".ts", ".tsx", "/__init__.py", "/index.js", "/index.ts"]
    for candidate in candidates:
        for suffix in suffixes:
            path = f"{candidate}{suffix}"
            if path in known_paths:
                return known_paths[path]
    return ""


def _central_files(edges: list[tuple[str, str]]) -> list[str]:
    inbound = Counter(target for _, target in edges if "/" in target or "." in target)
    outbound = Counter(source for source, _ in edges)
    ranked = sorted(
        set(inbound) | set(outbound),
        key=lambda path: (-(inbound[path] * 2 + outbound[path]), path),
    )
    return ranked[:20]
