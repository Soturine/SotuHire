import json
from pathlib import Path
from typing import cast

from modules.github_analyzer.context_builder import build_analysis_context
from modules.github_analyzer.dependency_graph import build_dependency_graph
from modules.github_analyzer.repository_models import (
    RepositoryAnalysisInput,
    RepositoryDetectedSignals,
    RepositoryMetadata,
    SelectedRepositoryFile,
)


def test_context_builder_includes_metadata_tree_files_signals_and_target_context() -> None:
    metadata = RepositoryMetadata.model_validate_json(
        Path("tests/fixtures/github_repos/repo_metadata.json").read_text(encoding="utf-8")
    )
    files = [
        SelectedRepositoryFile.model_validate(item)
        for item in json.loads(
            Path("tests/fixtures/github_repos/selected_files.json").read_text(encoding="utf-8")
        )
    ]
    signals = RepositoryDetectedSignals(has_readme=True, has_tests=True)
    graph = build_dependency_graph(files)

    payload = build_analysis_context(
        metadata=metadata,
        directory_tree=".\n|-- README.md",
        selected_files=files,
        detected_signals=signals,
        dependency_graph=graph,
        analysis_input=RepositoryAnalysisInput(
            mode="job_alignment",
            target_role="Backend Python",
            target_job={"required": ["Python", "FastAPI"]},
        ),
    )

    analysis_context = cast(dict[str, object], payload["analysis_context"])
    detected_signals = cast(dict[str, object], payload["detected_signals"])
    selected_files = cast(list[dict[str, object]], payload["selected_files"])

    assert payload["repository_structure"] == ".\n|-- README.md"
    assert analysis_context["mode"] == "job_alignment"
    assert detected_signals["has_tests"] is True
    assert str(selected_files[0]["content"]).startswith("# Career Lab")
