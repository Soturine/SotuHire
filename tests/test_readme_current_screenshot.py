from pathlib import Path


def test_readme_references_current_web_screenshots_and_changelog():
    readme = Path("README.md").read_text(encoding="utf-8")
    screenshots = [
        Path("docs/assets/screenshots/sotuhire-v1.7-web-walkthrough.gif"),
        Path("docs/assets/screenshots/sotuhire-v1.7-web-home.png"),
        Path("docs/assets/screenshots/sotuhire-v1.7-web-dashboard.png"),
        Path("docs/assets/screenshots/sotuhire-v1.7-web-sources-inbox.png"),
        Path("docs/assets/screenshots/sotuhire-v1.7-web-import-csv.png"),
        Path("docs/assets/screenshots/sotuhire-v1.7-web-kanban-source.png"),
        Path("docs/assets/screenshots/sotuhire-v1.7-web-extension-history.png"),
        Path("docs/assets/screenshots/sotuhire-v1.7-web-settings-ai.png"),
    ]

    for screenshot in screenshots:
        assert str(screenshot).replace("\\", "/") in readme
        assert screenshot.exists()
        assert 10_000 < screenshot.stat().st_size < 2_000_000
    assert readme.count("docs/assets/screenshots/") == len(screenshots)
    assert "[Changelog](CHANGELOG.md)" in readme
