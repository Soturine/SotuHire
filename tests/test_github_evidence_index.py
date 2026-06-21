from modules.github_analyzer.dependency_graph import DependencyGraphSummary
from modules.github_analyzer.evidence_index import build_evidence_index, has_critical_secret
from modules.github_analyzer.repository_models import (
    RepositoryDetectedSignals,
    RepositoryIdentity,
    RepositoryMetadata,
    SelectedRepositoryFile,
)


def test_evidence_index_tracks_presence_content_and_secret_flags() -> None:
    metadata = RepositoryMetadata(
        identity=RepositoryIdentity(
            owner="example", name="repo", url="https://github.com/example/repo"
        )
    )
    signals = RepositoryDetectedSignals(
        has_readme=True,
        has_tests=True,
        doc_paths=["README.md"],
        test_paths=["tests/test_app.py"],
    )
    files = [
        SelectedRepositoryFile(
            path="README.md",
            content="TOKEN='ghp_1234567890123456789012345'",
            reason_selected="readme",
            fetched=True,
        )
    ]

    evidence = build_evidence_index(
        metadata=metadata,
        signals=signals,
        selected_files=files,
        dependency_graph=DependencyGraphSummary(central_files=["README.md"]),
    )

    assert any(item.source_file == "tests/test_app.py" for item in evidence)
    assert any(item.evidence_type == "dependency" for item in evidence)
    assert has_critical_secret(evidence) is True
