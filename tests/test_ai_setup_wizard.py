from modules.ai import setup


def test_setup_status_explains_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr(setup, "_read_local_secrets", lambda path=setup.DEFAULT_SECRETS_PATH: {})

    status = setup.gemini_setup_status()

    assert not status.available
    assert status.reason == "chave ausente"
    assert "Usando análise local" in status.message


def test_setup_saves_non_versioned_local_configuration(tmp_path, monkeypatch):
    target = tmp_path / ".streamlit" / "secrets.toml"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    saved = setup.save_local_ai_config("fake-secret", path=target)

    assert saved == target
    assert "fake-secret" in target.read_text(encoding="utf-8")
    assert setup.gemini_api_key() == "fake-secret"


def test_fake_key_failure_is_friendly(monkeypatch):
    monkeypatch.setattr(setup, "gemini_sdk_installed", lambda: True)

    def fail(*args, **kwargs):
        raise RuntimeError("invalid api key")

    from modules.ai.providers.gemini_provider import GeminiProvider

    monkeypatch.setattr(GeminiProvider, "analyze", fail)
    result = setup.test_gemini_connection("fake-key")

    assert not result.success
    assert result.message == "Não foi possível autenticar no Gemini."
    assert "invalid api key" in result.detail
