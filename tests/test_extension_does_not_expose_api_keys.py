from pathlib import Path


def test_extension_has_no_provider_key_or_direct_provider_call():
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    content = Path("browser-extension/content.js").read_text(encoding="utf-8")
    injected = Path("browser-extension/github_injected.js").read_text(encoding="utf-8")
    html = Path("browser-extension/popup.html").read_text(encoding="utf-8")

    serialized = "\n".join([popup, content, injected, html])
    assert "standaloneGeminiKey" not in serialized
    assert "x-goog-api-key" not in serialized
    assert "generativelanguage.googleapis.com" not in serialized
    assert "Gemini API Key da extensao" not in serialized
    assert "body: body ? JSON.stringify(body)" in popup
    assert "localStorage" not in content
    assert "sessionStorage" not in content


def test_extension_keeps_failed_companion_actions_for_retry():
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    html = Path("browser-extension/popup.html").read_text(encoding="utf-8")

    assert "pendingCompanionActions" in popup
    assert "queuePendingAction" in popup
    assert "retryPending" in popup
    assert 'data-action="retry-pending"' in html
    assert "copiar o texto ou acumular um lote offline" in popup
