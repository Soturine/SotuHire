from modules.portfolio import ProjectAnalysisPayload, analyze_project


def test_repository_quality_rewards_docs_tests_architecture_and_commits():
    strong = analyze_project(
        ProjectAnalysisPayload(
            url="https://github.example/example/strong",
            page_type="github_repo",
            readme_text="Installation Usage Architecture " * 30,
            files_sampled=[
                "README.md",
                "src/app.py",
                "modules/service.py",
                "tests/test_app.py",
                "docs/architecture.md",
                ".github/workflows/ci.yml",
            ],
            commit_messages=["feat: add service", "test: cover service", "docs: explain service"],
            languages=["Python"],
        )
    )
    weak = analyze_project(
        ProjectAnalysisPayload(
            url="https://github.example/example/weak",
            page_type="github_repo",
        )
    )

    assert strong.repository_quality_score > weak.repository_quality_score
