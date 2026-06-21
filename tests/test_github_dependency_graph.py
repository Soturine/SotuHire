import json
from pathlib import Path

from modules.github_analyzer.dependency_graph import build_dependency_graph
from modules.github_analyzer.repository_models import SelectedRepositoryFile


def test_dependency_graph_detects_python_import_edges() -> None:
    files = [
        SelectedRepositoryFile.model_validate(item)
        for item in json.loads(
            Path("tests/fixtures/github_repos/selected_files.json").read_text(encoding="utf-8")
        )
    ]

    graph = build_dependency_graph(files)

    assert ("modules/api.py", "modules/service.py") in graph.import_edges
    assert "modules/service.py" in graph.central_files


def test_dependency_graph_detects_javascript_import_edges() -> None:
    files = [
        SelectedRepositoryFile(
            path="src/index.ts",
            content="import { client } from './api/client';\nconst fs = require('fs');",
            reason_selected="source",
            language_hint="TypeScript",
            fetched=True,
        ),
        SelectedRepositoryFile(
            path="src/api/client.ts",
            content="export const client = {};",
            reason_selected="source",
            language_hint="TypeScript",
            fetched=True,
        ),
    ]

    graph = build_dependency_graph(files)

    assert ("src/index.ts", "src/api/client.ts") in graph.import_edges
