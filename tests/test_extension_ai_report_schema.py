from modules.portfolio import ProjectAnalysisPayload, ProjectAnalysisReport, analyze_project


def test_public_repo_becomes_full_typed_report():
    report = analyze_project(
        ProjectAnalysisPayload(
            url="https://github.example/example/repo",
            owner="example",
            repo="repo",
            title="Example Repo",
            page_type="github_repo",
            readme_text="Installation Usage Architecture Python FastAPI",
            files_sampled=["README.md", "pyproject.toml", "src/app.py", "tests/test_app.py"],
            commit_messages=["feat: add API", "test: cover API"],
            languages=["Python"],
            topics=["FastAPI"],
        )
    )

    assert isinstance(report, ProjectAnalysisReport)
    assert report.overall_score > 0
    assert report.grade in {"A", "B", "C", "D", "F"}
    assert report.stack
    assert report.resume_highlights
