from pathlib import Path


def test_standalone_mode_has_local_fallback_providers_and_deep_limit():
    injected = Path("browser-extension/github_injected.js").read_text(encoding="utf-8")
    analyzer = Path("browser-extension/project_analysis.js").read_text(encoding="utf-8")
    background = Path("browser-extension/background.js").read_text(encoding="utf-8")

    assert "SOTUHIRE_AI_ANALYZE" in injected
    assert "SotuHireProjectAnalyzer.analyze(enriched)" in background
    assert 'provider_used: "local-browser"' in background
    assert "analyzeWithGemini" in background
    assert "analyzeWithOpenAi" in background
    assert "standaloneGeminiKey" not in injected
    assert "chrome.permissions.request" not in injected
    assert "deep ? 200 : 80" in injected
    assert "deep ? 100 : 30" in injected
    assert "overall_score" in analyzer
    assert "commit_analysis" in analyzer


def test_extension_public_exam_capture_action_is_backend_local_only():
    popup_html = Path("browser-extension/popup.html").read_text(encoding="utf-8")
    popup_js = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    content_js = Path("browser-extension/content.js").read_text(encoding="utf-8")

    assert 'data-action="capture-public-exam"' in popup_html
    assert '"/capture/public-exam"' in popup_js
    assert 'kind: "public_exam"' in popup_js
    assert 'kind: "job"' in content_js
    assert "document.cookie" not in content_js
    assert "localStorage" not in content_js
    assert "sessionStorage" not in content_js
