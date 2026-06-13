from modules.ai.providers.gemini_provider import GeminiProvider
from modules.ai.structured_analysis import get_provider


def test_llm_provider_remains_a_compatible_alias(monkeypatch):
    monkeypatch.delenv("DEFAULT_AI_PROVIDER", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    assert isinstance(get_provider(), GeminiProvider)


def test_new_provider_variable_has_precedence(monkeypatch):
    monkeypatch.setenv("DEFAULT_AI_PROVIDER", "local")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    assert get_provider().name == "local"


def test_llm_model_remains_a_compatible_alias(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("LLM_MODEL", "gemini-legacy-alias")

    assert GeminiProvider(api_key="test").model == "gemini-legacy-alias"
