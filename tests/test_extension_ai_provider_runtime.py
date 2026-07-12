import json
import subprocess


def test_extension_provider_runtime_uses_selected_models_and_session_secrets():
    result = subprocess.run(
        [
            "node",
            "tests/fixtures/extension/background_harness.js",
            "browser-extension",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["geminiProvider"] == "gemini"
    assert payload["geminiModel"] == "gemini-new-test"
    assert payload["openaiProvider"] == "openai"
    assert payload["openaiModel"] == "gpt-4.1-mini"
    assert payload["sessionKeyCount"] == 1
    assert payload["vaultKeyCount"] == 1
    assert payload["localSecretCount"] == 0
    assert any(
        "gemini-new-test:generateContent" in call["url"] and call["hasGeminiHeader"]
        for call in payload["calls"]
    )
    assert any(
        call["url"].endswith("/responses") and call["model"] == "gpt-4.1-mini"
        for call in payload["calls"]
    )
