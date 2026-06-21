import json
from pathlib import Path
from typing import cast

from modules.ai.json_guard import validate_ai_json
from modules.ai.prompt_loader import default_prompt_registry
from modules.github_analyzer.analyzer_service import (
    analyze_github_repository,
    project_report_from_github_analysis,
)
from modules.github_analyzer.exceptions import GitHubApiError
from modules.github_analyzer.github_client import GitHubClient
from modules.github_analyzer.repository_models import (
    RepositoryIdentity,
    RepositoryMetadata,
    RepositoryTree,
    SelectedRepositoryFile,
)
from modules.github_analyzer.schemas import GitHubRepoAnalysisOutput
from modules.local_api.app import LocalCompanionService
from modules.portfolio.schemas import ProjectAnalysisPayload


class FakeGitHubClient(GitHubClient):
    def __init__(self) -> None:
        self.contents = {
            "README.md": "# Career Lab\n\nFastAPI project with setup and usage.",
            "pyproject.toml": "[project]\ndependencies=['fastapi','pytest']",
            ".github/workflows/ci.yml": "run: pytest",
            "modules/api.py": "from modules.service import build_report\n",
            "modules/service.py": "def build_report():\n    return {}\n",
            "tests/test_service.py": "def test_service():\n    assert True\n",
            "docs/usage.md": "Usage docs",
        }

    def repository_identity(self, value: str) -> RepositoryIdentity:
        return RepositoryIdentity(owner="example", name="career-lab", url=value)

    def get_metadata(self, owner: str, repo: str) -> RepositoryMetadata:
        return RepositoryMetadata.model_validate_json(
            Path("tests/fixtures/github_repos/repo_metadata.json").read_text(encoding="utf-8")
        )

    def get_tree(self, owner: str, repo: str, ref: str) -> RepositoryTree:
        data = json.loads(
            Path("tests/fixtures/github_repos/python_project_tree.json").read_text(encoding="utf-8")
        )
        return RepositoryTree.model_validate(data)

    def fetch_file(
        self,
        owner: str,
        repo: str,
        ref: str,
        file: SelectedRepositoryFile,
        *,
        max_chars: int = 12000,
    ) -> SelectedRepositoryFile:
        return file.model_copy(
            update={
                "content": self.contents.get(file.path, "")[:max_chars],
                "fetched": file.path in self.contents,
            }
        )


class FailingGitHubClient(FakeGitHubClient):
    def get_metadata(self, owner: str, repo: str) -> RepositoryMetadata:
        raise GitHubApiError("offline")


def test_analyzer_service_builds_report_without_real_github_call() -> None:
    report = analyze_github_repository(
        "https://github.com/example/career-lab",
        client=FakeGitHubClient(),
    )

    assert report.repository_identity.name == "career-lab"
    assert report.scores.overall_score > 0
    assert "README.md" in report.files_sampled
    assert report.evidence_index
    assert report.fallback_used is False


def test_analyzer_service_uses_fallback_payload_when_api_fails() -> None:
    payload = ProjectAnalysisPayload(
        url="https://github.com/example/career-lab",
        owner="example",
        repo="career-lab",
        page_type="github_repo",
        readme_text="# Career Lab",
        files_sampled=["README.md", "src/app.py"],
        languages=["Python"],
    )

    report = analyze_github_repository(
        payload.url,
        client=FailingGitHubClient(),
        fallback_payload=payload,
    )

    assert report.fallback_used is True
    assert report.provider_used == "local-fallback"


def test_github_repo_prompt_schema_is_registered_and_json_guard_validates_output() -> None:
    registry = default_prompt_registry()
    schema = registry.output_schema("github_repo_analysis_v2")
    payload = {
        "repository_identity": {
            "owner": "example",
            "name": "repo",
            "url": "https://github.com/example/repo",
        },
        "executive_summary": {"short_summary": "ok"},
        "dimension_scores": {"tests": 5, "security": 6},
        "final_verdict": {"one_sentence_verdict": "ok"},
    }

    result = validate_ai_json(json.dumps(payload), schema)

    data = cast(GitHubRepoAnalysisOutput, result.data)

    assert data.repository_identity.name == "repo"


def test_project_report_conversion_keeps_extension_contract() -> None:
    payload = ProjectAnalysisPayload(
        url="https://github.com/example/career-lab",
        owner="example",
        repo="career-lab",
        page_type="github_repo",
        files_sampled=["README.md"],
    )
    report = analyze_github_repository(payload.url, client=FakeGitHubClient())

    project_report = project_report_from_github_analysis(report, payload)

    assert project_report.overall_score == report.scores.overall_score
    assert project_report.files_sampled
    assert project_report.resume_highlights


def test_local_api_uses_github_analyzer_when_payload_requests_api(monkeypatch) -> None:
    called = {"value": False}

    def fake_analyze(*args, **kwargs):
        called["value"] = True
        return analyze_github_repository(
            "https://github.com/example/career-lab",
            client=FakeGitHubClient(),
        )

    monkeypatch.setattr("modules.local_api.app.analyze_github_repository", fake_analyze)
    service = LocalCompanionService()
    payload = ProjectAnalysisPayload(
        url="https://github.com/example/career-lab",
        owner="example",
        repo="career-lab",
        page_type="github_repo",
        files_sampled=["README.md"],
        analysis_result={"use_github_api": True},
    )

    response = service.analyze_project_capture(payload, save_to_memory=False)

    assert called["value"] is True
    assert cast(dict[str, object], response.model_dump())["report"]
