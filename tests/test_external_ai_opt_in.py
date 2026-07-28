from __future__ import annotations

import os
from typing import NoReturn

import pytest
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.provider_errors import ProviderCallError
from modules.ai.providers import GeminiProvider, OpenAIProvider
from modules.ai.schemas.analysis_insights import SafeAiInsightOutput
from modules.ai.tracing import record_ai_run
from modules.storage.ai_runs import AiRunStore

pytestmark = pytest.mark.external_ai


def _handle_provider_error(error: ProviderCallError) -> NoReturn:
    diagnostic = error.error
    if diagnostic.blocked_external_account:
        pytest.skip(
            "BLOCKED_EXTERNAL_ACCOUNT "
            f"provider={diagnostic.provider} category={diagnostic.category.value} "
            f"error_type={diagnostic.error_type} request_id={diagnostic.request_id or 'absent'}"
        )
    pytest.fail(
        "EXTERNAL_PROVIDER_ERROR "
        f"provider={diagnostic.provider} category={diagnostic.category.value} "
        f"error_type={diagnostic.error_type} request_id={diagnostic.request_id or 'absent'}"
    )


def test_real_gemini_ping_opt_in() -> None:
    api_key = os.getenv("SOTUHIRE_TEST_GEMINI_API_KEY", "").strip()
    if not api_key:
        pytest.skip("Set SOTUHIRE_TEST_GEMINI_API_KEY to run real Gemini provider tests.")

    try:
        result = GeminiProvider(api_key=api_key, model="gemini-2.5-flash").ping()
    except ProviderCallError as exc:
        _handle_provider_error(exc)

    assert result


def test_real_openai_ping_opt_in() -> None:
    api_key = os.getenv("SOTUHIRE_TEST_OPENAI_API_KEY", "").strip()
    if not api_key:
        pytest.skip("Set SOTUHIRE_TEST_OPENAI_API_KEY to run real OpenAI provider tests.")

    try:
        result = OpenAIProvider(api_key=api_key, model="gpt-4.1-mini").ping()
    except ProviderCallError as exc:
        _handle_provider_error(exc)

    assert result


def test_real_gemini_structured_output_and_safe_trace_opt_in(tmp_path, monkeypatch) -> None:
    api_key = os.getenv("SOTUHIRE_TEST_GEMINI_API_KEY", "").strip()
    if not api_key:
        pytest.skip("Set SOTUHIRE_TEST_GEMINI_API_KEY to run real Gemini provider tests.")
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    provider = GeminiProvider(api_key=api_key, model="gemini-2.5-flash")
    spec = default_prompt_registry().get("career_advice_v1")

    try:
        output = provider.generate_structured(
            spec,
            {
                "context": "Pessoa fictícia busca primeira oportunidade administrativa.",
                "evidence": "Curso fictício de planilhas concluído; sem experiência formal.",
            },
        )
    except ProviderCallError as exc:
        _handle_provider_error(exc)
    validated = SafeAiInsightOutput.model_validate(output)
    trace = record_ai_run(
        "career_advice",
        provider_requested="gemini",
        provider_used="gemini",
        model_requested=provider.model,
        model_used=provider.model,
        provider=provider,
        warnings=validated.warnings,
    )

    restored = AiRunStore(tmp_path / "sotuhire.db").get(trace.run_id)
    assert restored is not None
    assert restored.model_used == provider.model
    assert restored.schema_valid is True
    assert restored.total_tokens is None or restored.total_tokens > 0
    assert api_key.encode() not in (tmp_path / "sotuhire.db").read_bytes()


def test_real_openai_structured_output_and_safe_trace_opt_in(tmp_path, monkeypatch) -> None:
    api_key = os.getenv("SOTUHIRE_TEST_OPENAI_API_KEY", "").strip()
    if not api_key:
        pytest.skip("Set SOTUHIRE_TEST_OPENAI_API_KEY to run real OpenAI provider tests.")
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    provider = OpenAIProvider(api_key=api_key, model="gpt-4.1-mini")
    spec = default_prompt_registry().get("career_advice_v1")

    try:
        output = provider.generate_structured(
            spec,
            {
                "context": "Pessoa fictícia busca primeira oportunidade administrativa.",
                "evidence": "Curso fictício de planilhas concluído; sem experiência formal.",
            },
        )
    except ProviderCallError as exc:
        _handle_provider_error(exc)
    validated = SafeAiInsightOutput.model_validate(output)
    trace = record_ai_run(
        "career_advice",
        provider_requested="openai",
        provider_used="openai",
        model_requested=provider.model,
        model_used=provider.model,
        provider=provider,
        warnings=validated.warnings,
    )

    restored = AiRunStore(tmp_path / "sotuhire.db").get(trace.run_id)
    assert restored is not None
    assert restored.model_used == provider.model
    assert restored.schema_valid is True
    assert restored.total_tokens is None or restored.total_tokens > 0
    assert api_key.encode() not in (tmp_path / "sotuhire.db").read_bytes()
