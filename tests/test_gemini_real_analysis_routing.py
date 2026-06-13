from modules.ai.providers.gemini_provider import GeminiProvider
from modules.ai.providers.mock_provider import MockProvider
from modules.ai.structured_analysis import get_provider


def test_session_key_is_routed_to_gemini_provider():
    provider = get_provider("gemini", api_key="session-key", model="gemini-session-model")

    assert isinstance(provider, GeminiProvider)
    assert provider.name == "gemini"
    assert provider.api_key == "session-key"
    assert provider.model == "gemini-session-model"


def test_local_provider_remains_local_with_session_key():
    assert isinstance(get_provider("local", api_key="session-key"), MockProvider)
