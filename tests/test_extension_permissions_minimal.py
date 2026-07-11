import json
from pathlib import Path


def test_extension_permissions_are_scoped_to_features():
    manifest = json.loads(Path("browser-extension/manifest.json").read_text(encoding="utf-8"))

    assert set(manifest["permissions"]) == {"activeTab", "scripting", "storage"}
    assert set(manifest["host_permissions"]) == {
        "http://127.0.0.1:8765/*",
        "https://github.com/*",
    }
    assert "optional_host_permissions" not in manifest
    serialized = json.dumps(manifest)
    assert "<all_urls>" not in serialized
    assert "cookies" not in serialized
    assert "webRequest" not in serialized
    assert "generativelanguage.googleapis.com" not in serialized
