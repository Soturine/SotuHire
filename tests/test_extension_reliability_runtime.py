from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest
from modules.local_api import LocalCompanionApp
from scripts.package_extension import scan_for_secrets


def _run_node(harness: str) -> dict[str, Any]:
    result = subprocess.run(
        ["node", f"tests/fixtures/extension/{harness}", "browser-extension"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_queue_runtime_deduplicates_retries_and_exports_safely() -> None:
    result = _run_node("queue_runtime_harness.js")

    assert result == {
        "deduplicated": 1,
        "retryCount": 5,
        "state": "failed",
        "safeExport": True,
        "safeImport": True,
    }


def test_content_runtime_prioritizes_nested_schema_org_jobposting() -> None:
    capture = _run_node("content_jobposting_harness.js")

    assert capture["extraction_strategy"] == "schema_org_jobposting"
    assert capture["job_title"] == "Pessoa Desenvolvedora Backend"
    assert capture["company"] == "Empresa Exemplo"
    assert capture["location"] == "Recife, PE, Brasil"
    assert capture["description"] == "Construa APIs Python ."
    assert capture["structured_data"]["@type"].endswith("/JobPosting")


@pytest.mark.parametrize(
    "secret_value",
    [
        "AIza" + "A" * 28,
        "AQ." + "B" * 28,
        "sk-" + "C" * 28,
        "sk-" + "proj-" + "D" * 28,
    ],
)
def test_package_secret_scan_rejects_gemini_and_openai_patterns(
    tmp_path: Path, secret_value: str
) -> None:
    extension = tmp_path / "extension"
    shutil.copytree("browser-extension", extension)
    with (extension / "popup.js").open("a", encoding="utf-8") as handle:
        handle.write(f"\n// {secret_value}\n")

    with pytest.raises(ValueError, match="Possivel segredo"):
        scan_for_secrets(extension)


def test_popup_uses_versioned_handshake_contract() -> None:
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    manifest = json.loads(Path("browser-extension/manifest.json").read_text(encoding="utf-8"))

    assert manifest["version"] == "0.9.3"
    assert 'request("/handshake"' in popup
    assert "chrome.runtime.getManifest().version" in popup
    assert "handshake.compatible" in popup
    assert "handshake.warnings" in popup


def test_companion_handshake_negotiates_current_and_old_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    app = LocalCompanionApp(token="")

    status, current = app.handle("POST", "/handshake", body=b'{"extension_version":"0.9.3"}')
    old_status, old = app.handle("POST", "/handshake", body=b'{"extension_version":"0.8.9"}')

    assert status == 200
    assert current["extension_version"] == "0.9.3"
    assert current["companion_version"] == "1.9.7"
    assert current["compatible"] is True
    capabilities = cast(list[str], current["capabilities"])
    assert "queue.retry" in capabilities
    assert "jobposting.jsonld" in capabilities
    assert old_status == 200
    assert old["compatible"] is False
    assert old["warnings"]


def test_sotuhire_provider_fallback_is_explicit() -> None:
    background = Path("browser-extension/background.js").read_text(encoding="utf-8")

    assert "apiFallbackReason" in background
    assert "analysis_mode: apiFallbackReason" in background
    assert '? "fallback"' in background
    assert "fallback_used: Boolean(report.fallback_used || apiFallbackReason)" in background
