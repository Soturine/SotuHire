from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_extension_feedback_requires_a_persisted_trace_and_uses_safe_fields() -> None:
    background = (ROOT / "browser-extension" / "background.js").read_text(encoding="utf-8")
    injected = (ROOT / "browser-extension" / "github_injected.js").read_text(encoding="utf-8")

    assert 'message.type === "SOTUHIRE_AI_FEEDBACK"' in background
    assert "fetch(`${APP_API}/ai/feedback`" in background
    assert "if (!runId || !taskId)" in background
    assert 'type: "SOTUHIRE_AI_FEEDBACK"' in injected
    assert "currentReport?.run_id" in injected
    assert "unsupported_claim" in background
    assert (
        "extension_ai_report"
        not in background.split("async function submitAiFeedback", maxsplit=1)[1].split(
            "function normalizeSotuHireReport", maxsplit=1
        )[0]
    )
    assert (
        "apiKey"
        not in background.split("async function submitAiFeedback", maxsplit=1)[1].split(
            "function normalizeSotuHireReport", maxsplit=1
        )[0]
    )


def test_extension_feedback_version_is_093() -> None:
    manifest = (ROOT / "browser-extension" / "manifest.json").read_text(encoding="utf-8")
    popup = (ROOT / "browser-extension" / "popup.html").read_text(encoding="utf-8")

    assert '"version": "0.9.3"' in manifest
    assert "v0.9.3" in popup
