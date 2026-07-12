from pathlib import Path


def test_extension_keeps_provider_keys_out_of_content_scripts():
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    content = Path("browser-extension/content.js").read_text(encoding="utf-8")
    injected = Path("browser-extension/github_injected.js").read_text(encoding="utf-8")
    html = Path("browser-extension/popup.html").read_text(encoding="utf-8")
    background = Path("browser-extension/background.js").read_text(encoding="utf-8")

    serialized = "\n".join([popup, content, injected, html])
    assert "standaloneGeminiKey" not in serialized
    assert "x-goog-api-key" not in serialized
    assert "generativelanguage.googleapis.com" not in serialized
    assert "sotuhireExtensionSecret_" not in serialized
    assert "chrome.storage.session" in background
    assert "chrome.storage.sync" not in background
    assert 'indexedDB.open("sotuhire-extension-vault"' in background
    assert 'credentials: "omit"' in background
    assert '"x-goog-api-key": key' in background
    assert "Authorization: `Bearer ${key}`" in background
    assert "body: body ? JSON.stringify(body)" in popup
    assert "localStorage" not in content
    assert "sessionStorage" not in content


def test_extension_model_selection_drives_real_provider_request():
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    background = Path("browser-extension/background.js").read_text(encoding="utf-8")

    assert "model: aiModel.value" in popup
    assert "listGeminiModels" in background
    assert "listOpenAiModels" in background
    assert "analyzeWithGemini(key, model" in background
    assert "analyzeWithOpenAi(key, model" in background
    assert "SOTUHIRE_GITHUB_ENRICH" in background
    assert "http://127.0.0.1:8787/api/v1" in background
    assert "provider_requested:" in background
    assert "data.provider_requested" in background


def test_extension_keeps_failed_companion_actions_for_retry():
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    html = Path("browser-extension/popup.html").read_text(encoding="utf-8")

    assert "pendingCompanionActions" in popup
    assert "queuePendingAction" in popup
    assert "retryPending" in popup
    assert 'data-action="retry-pending"' in html
    assert "copiar o texto ou acumular um lote offline" in popup
