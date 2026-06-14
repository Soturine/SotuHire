import json
from pathlib import Path


def test_github_button_is_injected_for_repo_tree_blob_and_profile_pages():
    manifest = json.loads(Path("browser-extension/manifest.json").read_text(encoding="utf-8"))
    script = Path("browser-extension/github_injected.js").read_text(encoding="utf-8")

    content_script = manifest["content_scripts"][0]
    assert content_script["matches"] == ["https://github.com/*"]
    assert "github_injected.js" in content_script["js"]
    assert "sotuhire-repo-button" in script
    assert "SotuHire AI" in script
    assert "Analyze GitHub Profile with SotuHire" in script
    assert "(?:tree|blob)" in script
    assert "MutationObserver" in script
    assert "preferred || fallback" in script
