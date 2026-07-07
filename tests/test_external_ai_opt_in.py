from __future__ import annotations

import os

import pytest
from modules.ai.providers import GeminiProvider, OpenAIProvider

pytestmark = pytest.mark.external_ai


def test_real_gemini_ping_opt_in() -> None:
    api_key = os.getenv("SOTUHIRE_TEST_GEMINI_API_KEY", "").strip()
    if not api_key:
        pytest.skip("Set SOTUHIRE_TEST_GEMINI_API_KEY to run real Gemini provider tests.")

    result = GeminiProvider(api_key=api_key, model="gemini-2.5-flash").ping()

    assert result


def test_real_openai_ping_opt_in() -> None:
    api_key = os.getenv("SOTUHIRE_TEST_OPENAI_API_KEY", "").strip()
    if not api_key:
        pytest.skip("Set SOTUHIRE_TEST_OPENAI_API_KEY to run real OpenAI provider tests.")

    result = OpenAIProvider(api_key=api_key, model="gpt-5-mini").ping()

    assert result
