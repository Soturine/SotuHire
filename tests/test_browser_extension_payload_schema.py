from pathlib import Path

from modules.local_api import BrowserCapturePayload


def test_extension_payload_contract_and_no_api_key_storage():
    content = Path("browser-extension/content.js").read_text(encoding="utf-8")
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    payload = BrowserCapturePayload(
        page_title="Vaga fictícia",
        url="https://jobs.example/1",
        visible_text="Python e SQL",
    )

    assert payload.collection_method == "browser_assisted_capture"
    assert "captured_at" in content
    assert "applications" in content
    assert "standaloneGeminiKey" in popup
    assert "standaloneGeminiKey" not in content
    assert "SOTUHIRE_PROJECT" in content
