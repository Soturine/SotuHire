from pathlib import Path


def test_standalone_key_is_never_added_to_local_companion_payload():
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    content = Path("browser-extension/content.js").read_text(encoding="utf-8")

    assert "standaloneGeminiKey" in popup
    assert '"x-goog-api-key": standaloneGeminiKey.value' in popup
    assert "standaloneGeminiKey" not in content
    assert "body: body ? JSON.stringify(body)" in popup
    assert "localStorage" not in content
    assert "sessionStorage" not in content
