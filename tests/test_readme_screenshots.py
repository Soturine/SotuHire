from pathlib import Path

SCREENSHOTS = [
    "sotuhire-v0.6-home.png",
    "sotuhire-v0.6-resume.png",
    "sotuhire-v0.6-job.png",
    "sotuhire-v0.6-result.png",
    "sotuhire-v0.6-dashboard.png",
    "sotuhire-v0.6-ai-setup.png",
]


def test_readme_references_existing_optimized_screenshots():
    readme = Path("README.md").read_text(encoding="utf-8")
    root = Path("docs/assets/screenshots")

    for name in SCREENSHOTS:
        path = root / name
        assert str(path).replace("\\", "/") in readme
        assert path.exists()
        assert 10_000 < path.stat().st_size < 500_000
