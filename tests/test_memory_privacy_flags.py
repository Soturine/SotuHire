from modules.memory import MemoryPrivacySettings


def test_memory_is_local_by_default_and_gemini_sharing_is_opt_in():
    settings = MemoryPrivacySettings()

    assert settings.use_memory
    assert not settings.send_relevant_context_to_gemini
