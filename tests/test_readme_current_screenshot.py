from pathlib import Path


def test_readme_references_current_web_screenshots_and_changelog():
    readme = Path("README.md").read_text(encoding="utf-8")
    screenshots = [
        Path("docs/assets/screenshots/sotuhire-web-product-walkthrough.gif"),
        Path("docs/assets/screenshots/sotuhire-web-profile.png"),
        Path("docs/assets/screenshots/sotuhire-web-match.png"),
        Path("docs/assets/screenshots/sotuhire-web-radar-schedules.png"),
        Path("docs/assets/screenshots/sotuhire-web-notifications.png"),
        Path("docs/assets/screenshots/sotuhire-web-tracker.png"),
        Path("docs/assets/screenshots/sotuhire-web-sources.png"),
        Path("docs/assets/screenshots/sotuhire-web-profile-lattes.png"),
        Path("docs/assets/screenshots/sotuhire-web-extension-profile-candidates.png"),
        Path("docs/assets/screenshots/sotuhire-web-settings-ai.png"),
    ]

    for screenshot in screenshots:
        assert str(screenshot).replace("\\", "/") in readme
        assert screenshot.exists()
        assert 10_000 < screenshot.stat().st_size < 2_000_000
    assert readme.count("docs/assets/screenshots/") == len(screenshots)
    assert "[Changelog](CHANGELOG.md)" in readme
    assert "release-v1.9.2" in readme
    assert "Frontend moderno v1.9.0" not in readme
    assert "API local v1.9.0" not in readme
    assert "Na v1.8.2" not in readme
    for link in [
        "docs/",
        "docs/01-product/roadmap.md",
        "docs/01-product/vision.md",
        "docs/01-product/multi-domain-product-strategy.md",
        "docs/02-architecture/module-integration-map.md",
        "docs/02-architecture/career-context-engine.md",
        "docs/02-architecture/extension-profile-bridge.md",
        "docs/02-architecture/public-exams-foundation.md",
        "docs/04-ai/prompt-catalog.md",
        "docs/04-ai/prompts/profile-lattes-extractor-v1.md",
        "docs/04-ai/career-memory-rag.md",
        "docs/06-engineering/security-privacy.md",
        "docs/07-development/v1.9.2-lattes-ai-universal-profile.md",
        "docs/releases/v1.9.2.md",
        "CHANGELOG.md",
        "browser-extension/README.md",
        "apps/web/README.md",
    ]:
        assert link in readme
