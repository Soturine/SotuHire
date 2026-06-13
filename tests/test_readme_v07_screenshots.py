from pathlib import Path

EXPECTED = [
    "sotuhire-v0.7-quick-mode.png",
    "sotuhire-v0.7-advanced-mode.png",
    "sotuhire-v0.7-collect-jobs.png",
    "sotuhire-v0.7-collected-opportunities.png",
    "sotuhire-v0.7-search-intelligence.png",
    "sotuhire-v0.7-hidden-radar.png",
    "sotuhire-v0.7-result.png",
    "sotuhire-v0.7-dashboard.png",
]


def test_readme_references_existing_v07_screenshots():
    readme = Path("README.md").read_text(encoding="utf-8")
    for name in EXPECTED:
        path = Path("docs/assets/screenshots") / name
        assert str(path).replace("\\", "/") in readme
        assert path.exists()
        assert 10_000 < path.stat().st_size < 600_000
