from pathlib import Path


def test_readme_references_one_current_screenshot_and_changelog():
    readme = Path("README.md").read_text(encoding="utf-8")
    screenshot = Path("docs/assets/screenshots/sotuhire-v0.7-advanced-mode.png")

    assert str(screenshot).replace("\\", "/") in readme
    assert readme.count("docs/assets/screenshots/") == 1
    assert "[Changelog](CHANGELOG.md)" in readme
    assert screenshot.exists()
    assert 10_000 < screenshot.stat().st_size < 600_000
