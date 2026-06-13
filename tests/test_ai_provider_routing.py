from modules.ai.providers.gemini_provider import GeminiProvider
from modules.ai.structured_analysis import analyze_structured, get_provider


def test_default_ai_provider_selects_gemini(monkeypatch):
    monkeypatch.setenv("DEFAULT_AI_PROVIDER", "gemini")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    assert isinstance(get_provider(), GeminiProvider)


def test_gemini_failure_reports_actual_provider_and_fallback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = analyze_structured("Python", "Vaga Python", provider=GeminiProvider(api_key=""))

    assert result.requested_provider == "gemini"
    assert result.provider == "local"
    assert result.fallback_used
    assert "Provider usado: Análise local" in result.warning
    assert "Fallback usado" in result.warning
