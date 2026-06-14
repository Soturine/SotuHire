from pathlib import Path


def test_standalone_mode_has_local_fallback_optional_key_and_deep_limit():
    injected = Path("browser-extension/github_injected.js").read_text(encoding="utf-8")
    analyzer = Path("browser-extension/project_analysis.js").read_text(encoding="utf-8")

    assert "SotuHireProjectAnalyzer.analyze(project)" in injected
    assert 'saved.standaloneGeminiKey ? "gemini-standalone" : "local-browser"' in injected
    assert "chrome.permissions.request" in injected
    assert "deep ? 200 : 80" in injected
    assert "deep ? 100 : 30" in injected
    assert "overall_score" in analyzer
    assert "commit_analysis" in analyzer
