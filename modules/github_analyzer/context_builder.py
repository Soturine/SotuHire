"""Build structured context payloads for GitHub repository analysis."""

from __future__ import annotations

from modules.github_analyzer.dependency_graph import DependencyGraphSummary
from modules.github_analyzer.repository_models import (
    RepositoryAnalysisInput,
    RepositoryDetectedSignals,
    RepositoryMetadata,
    SelectedRepositoryFile,
)


def build_analysis_context(
    *,
    metadata: RepositoryMetadata,
    directory_tree: str,
    selected_files: list[SelectedRepositoryFile],
    detected_signals: RepositoryDetectedSignals,
    dependency_graph: DependencyGraphSummary | None = None,
    analysis_input: RepositoryAnalysisInput | None = None,
) -> dict[str, object]:
    """Build the prompt/provider payload from collected repository evidence."""
    context = analysis_input or RepositoryAnalysisInput()
    graph = dependency_graph or DependencyGraphSummary()
    return {
        "repository": {
            **metadata.model_dump(mode="json"),
            "owner": metadata.identity.owner,
            "name": metadata.identity.name,
            "url": metadata.identity.url,
            "default_branch": metadata.identity.default_branch,
            "ref_sha": metadata.identity.ref_sha,
        },
        "analysis_context": context.model_dump(mode="json"),
        "detected_signals": detected_signals.model_dump(mode="json"),
        "repository_structure": directory_tree,
        "selected_files": [
            {
                "path": file.path,
                "reason_selected": file.reason_selected,
                "size": file.size,
                "language_hint": file.language_hint,
                "fetched": file.fetched,
                "truncated": file.truncated,
                "content": file.content,
            }
            for file in selected_files
        ],
        "dependency_graph": graph.model_dump(mode="json"),
    }


def summarize_selected_files(files: list[SelectedRepositoryFile]) -> list[str]:
    """Return stable sampled file paths for legacy report compatibility."""
    return [file.path for file in files]
