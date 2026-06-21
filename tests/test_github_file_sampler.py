import json
from pathlib import Path

from modules.github_analyzer.file_sampler import select_repository_files
from modules.github_analyzer.repository_models import RepositoryTree


def _tree(name: str) -> RepositoryTree:
    data = json.loads(Path(f"tests/fixtures/github_repos/{name}").read_text(encoding="utf-8"))
    return RepositoryTree.model_validate(data)


def test_file_sampler_prioritizes_readme_manifests_workflows_source_and_tests() -> None:
    selected = select_repository_files(_tree("python_project_tree.json"), max_files=6)
    paths = [file.path for file in selected]

    assert paths[:3] == ["README.md", "pyproject.toml", ".env.example"]
    assert ".github/workflows/ci.yml" in paths
    assert "modules/api.py" in paths
    assert "dist/bundle.js" not in paths
    assert "assets/logo.png" not in paths


def test_file_sampler_respects_total_context_budget() -> None:
    selected = select_repository_files(
        _tree("python_project_tree.json"),
        max_files=40,
        max_total_chars=2000,
    )

    assert selected
    assert sum(min(file.size or 0, 12_000) for file in selected) <= 3000
