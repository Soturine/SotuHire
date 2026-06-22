from pathlib import Path


def test_readme_references_current_streamlit_screenshots_and_changelog():
    readme = Path("README.md").read_text(encoding="utf-8")
    screenshots = [
        Path("docs/assets/screenshots/sotuhire-v1.1-streamlit-home.png"),
        Path("docs/assets/screenshots/sotuhire-v1.1-streamlit-match.png"),
        Path("docs/assets/screenshots/sotuhire-v1.1-streamlit-dashboard.png"),
    ]

    for screenshot in screenshots:
        assert str(screenshot).replace("\\", "/") in readme
        assert screenshot.exists()
        assert 10_000 < screenshot.stat().st_size < 600_000
    assert readme.count("docs/assets/screenshots/") == len(screenshots)
    assert "[Changelog](CHANGELOG.md)" in readme
