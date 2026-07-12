import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_release_versions_are_aligned_and_extension_is_independent():
    manifest = json.loads(_read("browser-extension/manifest.json"))
    web_package = json.loads(_read("apps/web/package.json"))

    assert manifest["version"] == "0.9.1"
    assert web_package["version"] == "1.9.5"
    assert 'version = "1.9.5"' in _read("pyproject.toml")
    assert 'API_VERSION = "1.9.5"' in _read("apps/api/config.py")
    assert "https://generativelanguage.googleapis.com/*" in manifest.get("host_permissions", [])
    assert "https://api.openai.com/*" in manifest.get("host_permissions", [])

    extension_source = "\n".join(
        _read(path)
        for path in [
            "browser-extension/popup.html",
            "browser-extension/popup.js",
            "browser-extension/github_injected.js",
        ]
    )
    assert "sotuhireExtensionSecret_" not in extension_source
    assert "GEMINI_API_KEY" not in extension_source
    assert "generativelanguage.googleapis.com" not in extension_source
    assert "pendingCompanionActions" in extension_source


def test_demo_has_seven_coherent_personas_and_safe_restore():
    personas = _read("apps/web/src/mocks/personas.ts")
    settings = _read("apps/web/src/routes/settings.tsx")
    persona_ids = re.findall(r'^\s{4}id: "([^"]+)",$', personas, flags=re.MULTILINE)

    assert persona_ids == [
        "engineering-student",
        "nursing",
        "researcher",
        "teacher",
        "career-transition",
        "public-exam",
        "designer",
    ]
    assert "restoreDemoPersona();" in settings
    assert "Restaurar dados de demonstração" in settings
    assert 'mode === "demo"' in settings


def test_v195_docs_and_real_walkthrough_assets_are_present():
    required_docs = [
        "docs/02-architecture/v1.9.5-integration-audit-matrix.md",
        "docs/02-architecture/data-lineage-and-deduplication.md",
        "docs/07-development/v1.9.5-product-qa-demo-portfolio.md",
        "docs/07-development/v1.9.5-clean-install-checklist.md",
        "docs/07-development/v1.9.5-manual-acceptance-test.md",
        "docs/09-portfolio/demo-script.md",
        "docs/09-portfolio/portfolio-case-study.md",
        "docs/releases/v1.9.5.md",
    ]
    for relative_path in required_docs:
        assert (ROOT / relative_path).stat().st_size > 300

    capture_script = _read("scripts/capture_web_walkthrough.py")
    web_assets = re.findall(r'"(sotuhire-web-[^"]+\.(?:png|gif))"', capture_script)
    assert len(set(web_assets)) == 21
    for filename in set(web_assets):
        assert (ROOT / "docs/assets/screenshots" / filename).stat().st_size > 10_000

    extension_assets = re.findall(
        r'_action\(page, "[^"]+", "([^"]+\.png)"\)',
        _read("scripts/capture_extension_screenshots.py"),
    )
    extension_assets.extend(
        ["popup-main.png", "ai-provider-setup.png", "github-analysis-modal.png"]
    )
    assert len(set(extension_assets)) == 10
    for filename in set(extension_assets):
        assert (ROOT / "docs/assets/screenshots/extension" / filename).stat().st_size > 10_000
