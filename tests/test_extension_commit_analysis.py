from modules.portfolio.commit_analysis import analyze_commits


def test_commit_analysis_rewards_clear_conventional_messages():
    report = analyze_commits(
        [
            "feat: add local project analyzer",
            "fix(api): validate project payload",
            "docs: explain repository report",
            "update",
        ]
    )

    assert report.commit_quality_score >= 60
    assert report.conventional_ratio == 0.75
    assert report.generic_messages == ["update"]
    assert report.relevant_messages
