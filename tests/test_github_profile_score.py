from modules.portfolio import ProjectAnalysisPayload, analyze_project


def test_github_profile_score_uses_languages_and_topics():
    report = analyze_project(
        ProjectAnalysisPayload(
            url="https://github.example/example",
            owner="example",
            page_type="github_profile",
            languages=["Python", "TypeScript", "SQL"],
            topics=["automation", "iot"],
        )
    )

    assert report.github_profile_score >= 70
