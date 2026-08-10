import json
from pathlib import Path


def test_extension_v0100_has_local_theme_locale_and_help() -> None:
    manifest = json.loads(Path("browser-extension/manifest.json").read_text(encoding="utf-8"))
    popup = Path("browser-extension/popup.html").read_text(encoding="utf-8")
    runtime = Path("browser-extension/popup.js").read_text(encoding="utf-8")

    assert manifest["version"] == "0.10.0"
    assert 'id="ui-locale"' in popup
    assert 'id="theme-toggle"' in popup
    assert 'class="help-panel"' in popup
    assert "uiPreferences" in runtime
    assert "chrome.storage.local.set({ uiPreferences })" in runtime
    assert "data-theme" not in popup
