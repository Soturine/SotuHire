import json
from pathlib import Path

from modules.github_analyzer.repository_models import RepositoryTree
from modules.github_analyzer.tree_builder import build_directory_tree, detect_repository_signals


def _tree(name: str) -> RepositoryTree:
    data = json.loads(Path(f"tests/fixtures/github_repos/{name}").read_text(encoding="utf-8"))
    return RepositoryTree.model_validate(data)


def test_tree_builder_generates_readable_tree_with_markers() -> None:
    output = build_directory_tree(_tree("python_project_tree.json"))

    assert "README.md [README]" in output
    assert "ci.yml [CI]" in output
    assert "test_service.py [TEST]" in output
    assert "node_modules" not in output
    assert "logo.png" in output


def test_detect_repository_signals_separates_presence_from_content() -> None:
    signals = detect_repository_signals(_tree("python_project_tree.json"))

    assert signals.has_readme is True
    assert signals.has_tests is True
    assert signals.has_ci is True
    assert signals.has_env_example is True
    assert signals.has_package_manifest is True
    assert signals.test_paths == ["tests/test_service.py"]
