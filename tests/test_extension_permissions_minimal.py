import json
from pathlib import Path


def test_extension_permissions_are_scoped_to_features():
    manifest = json.loads(Path("browser-extension/manifest.json").read_text(encoding="utf-8"))

    assert set(manifest["permissions"]) == {"activeTab", "scripting", "storage"}
    assert set(manifest["host_permissions"]) == {
        "http://127.0.0.1:8765/*",
        "http://127.0.0.1:8787/*",
        "https://github.com/*",
        "https://api.github.com/*",
        "https://generativelanguage.googleapis.com/*",
        "https://api.openai.com/*",
    }
    assert "optional_host_permissions" not in manifest
    serialized = json.dumps(manifest)
    assert "<all_urls>" not in serialized
    assert "cookies" not in serialized
    assert "webRequest" not in serialized
    assert "api.github.com" in serialized
    assert "generativelanguage.googleapis.com" in serialized
    assert "api.openai.com" in serialized
