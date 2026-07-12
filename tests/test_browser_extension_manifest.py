import json
from pathlib import Path


def test_browser_extension_manifest_is_valid_and_minimal():
    manifest = json.loads(Path("browser-extension/manifest.json").read_text(encoding="utf-8"))

    assert manifest["manifest_version"] == 3
    assert set(manifest["permissions"]) == {"activeTab", "scripting", "storage"}
    assert set(manifest["host_permissions"]) == {
        "http://127.0.0.1:8765/*",
        "http://127.0.0.1:8787/*",
        "https://github.com/*",
        "https://api.github.com/*",
        "https://generativelanguage.googleapis.com/*",
        "https://api.openai.com/*",
    }
    assert manifest["background"]["service_worker"] == "background.js"
    assert Path("browser-extension/popup.html").exists()
    assert Path("browser-extension/content.js").exists()
