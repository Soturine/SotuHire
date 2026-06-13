from modules.ai.diagnostics import diagnose_gemini_error
from modules.ai.providers.gemini_provider import GeminiProvider
from modules.ai.setup import (
    test_gemini_simple as run_gemini_simple_test,
)
from modules.ai.setup import (
    test_gemini_structured as run_gemini_structured_test,
)


def test_invalid_argument_generates_actionable_diagnostic():
    diagnostic = diagnose_gemini_error(
        RuntimeError("400 INVALID_ARGUMENT: invalid JSON payload"),
        test_type="structured",
        model="gemini-2.5-flash",
        key_source="GEMINI_API_KEY",
        call_type="generate_content com response_json_schema",
    )

    assert diagnostic.code == "400 INVALID_ARGUMENT"
    assert diagnostic.category == "schema ou payload estruturado incompatível"
    assert "outro modelo" in diagnostic.suggestion
    assert "secret" not in diagnostic.model


def test_simple_and_structured_tests_call_different_provider_paths(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("modules.ai.setup.gemini_sdk_installed", lambda: True)
    monkeypatch.setattr(GeminiProvider, "ping", lambda self: calls.append("simple") or "ok")
    monkeypatch.setattr(
        GeminiProvider,
        "analyze",
        lambda self, *args, **kwargs: calls.append("structured"),
    )

    simple = run_gemini_simple_test("fake-key")
    structured = run_gemini_structured_test("fake-key")

    assert simple.success
    assert structured.success
    assert calls == ["simple", "structured"]
