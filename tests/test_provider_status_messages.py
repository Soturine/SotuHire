from modules.ai import setup
from modules.ai.providers.gemini_provider import GeminiProvider
from modules.ai.structured_analysis import analyze_structured, gemini_setup_warning, get_provider


def test_local_provider_is_the_default(monkeypatch):
    monkeypatch.delenv("DEFAULT_AI_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    assert get_provider().name == "local"


def test_google_api_key_remains_a_compatible_alias(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "legacy-google-key")

    assert GeminiProvider().api_key == "legacy-google-key"


def test_missing_key_and_runtime_failure_use_friendly_messages(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr(setup, "_read_local_secrets", lambda path=setup.DEFAULT_SECRETS_PATH: {})

    warning = gemini_setup_warning()
    result = analyze_structured("Python", "Vaga Python", provider=GeminiProvider(api_key=""))

    assert "Gemini indisponível. Usando análise local." in warning
    assert "Gemini falhou, então usei análise local." in result.warning
    assert result.provider == "local"
    assert result.fallback_used
