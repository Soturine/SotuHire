from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast

import pytest
from modules.ai.prompt_spec import PromptSpec
from modules.ai.provider_errors import (
    ProviderCallError,
    ProviderError,
    ProviderErrorCategory,
    ProviderRetryPolicy,
    classify_gemini_error,
    classify_openai_error,
    parse_retry_after,
    sanitize_provider_message,
)
from modules.ai.providers.gemini_provider import GeminiProvider, gemini_response_json_schema
from modules.ai.providers.openai_provider import OpenAIProvider
from modules.ai.schema_repair import (
    SchemaRepairError,
    repair_instructions,
    validate_with_single_repair,
)
from pydantic import BaseModel


class _StructuredSample(BaseModel):
    answer: str


def _prompt() -> PromptSpec:
    return PromptSpec(
        prompt_id="provider_reliability_test",
        version="1.0.0",
        system_prompt="Use somente o payload.",
        user_template="{context}",
        output_schema=_StructuredSample,
    )


@pytest.mark.parametrize(
    ("code", "error_type", "message", "category", "retryable"),
    [
        (
            "insufficient_quota",
            "insufficient_quota",
            "You exceeded your current quota.",
            ProviderErrorCategory.INSUFFICIENT_QUOTA,
            False,
        ),
        (
            "billing_not_active",
            "invalid_request_error",
            "Billing is not active.",
            ProviderErrorCategory.BILLING_REQUIRED,
            False,
        ),
        (
            "project_limit",
            "requests",
            "Project quota reached.",
            ProviderErrorCategory.PROJECT_LIMIT,
            False,
        ),
        (
            "organization_limit",
            "requests",
            "Organization limit reached.",
            ProviderErrorCategory.PROJECT_LIMIT,
            False,
        ),
        (
            "rate_limit_exceeded",
            "requests",
            "Too many requests.",
            ProviderErrorCategory.RATE_LIMIT,
            True,
        ),
    ],
)
def test_openai_429_categories_are_distinct(
    code: str,
    error_type: str,
    message: str,
    category: ProviderErrorCategory,
    retryable: bool,
) -> None:
    error = classify_openai_error(
        model="gpt-4.1-mini",
        status_code=429,
        headers={"x-request-id": "req_safe"},
        body={"error": {"code": code, "type": error_type, "message": message}},
        attempt=1,
        max_attempts=2,
    )

    assert error.category is category
    assert error.retryable is retryable
    assert error.request_id == "req_safe"
    assert error.error_code == code


def test_retry_after_seconds_and_http_date_are_supported() -> None:
    now = datetime.now(UTC)

    assert parse_retry_after("2.5", now=now) == 2.5
    parsed = parse_retry_after(
        (now + timedelta(seconds=10)).strftime("%a, %d %b %Y %H:%M:%S GMT"), now=now
    )
    assert parsed is not None
    assert 9 <= parsed <= 10


def test_retry_policy_respects_retry_after_jitter_and_cap() -> None:
    policy = ProviderRetryPolicy(
        max_attempts=2,
        base_delay_seconds=0.5,
        max_delay_seconds=4,
        jitter_ratio=0.25,
    )
    error = ProviderError(
        provider="openai",
        model="gpt-4.1-mini",
        category=ProviderErrorCategory.RATE_LIMIT,
        retryable=True,
        retry_after_seconds=2,
        attempt=1,
        max_attempts=2,
    )

    assert policy.delay_seconds(error, random_value=lambda: 1) == 2.5


def test_openai_retries_only_retryable_error_and_records_metadata() -> None:
    calls = 0
    sleeps: list[float] = []

    def transport(body: dict[str, object]) -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ProviderCallError(
                ProviderError(
                    provider="openai",
                    model="gpt-4.1-mini",
                    status_code=429,
                    error_code="rate_limit_exceeded",
                    error_type="requests",
                    category=ProviderErrorCategory.RATE_LIMIT,
                    retryable=True,
                    retry_after_seconds=1,
                    request_id="req_retry",
                    sanitized_message="Too many requests.",
                    attempt=1,
                    max_attempts=2,
                )
            )
        return {"id": "resp_safe", "output_text": json.dumps({"answer": "ok"})}

    provider = OpenAIProvider(
        api_key="test-only-value",
        model="gpt-4.1-mini",
        transport=transport,
        retry_policy=ProviderRetryPolicy(max_attempts=2, jitter_ratio=0),
        sleeper=sleeps.append,
    )

    result = cast(
        _StructuredSample,
        provider.generate_structured(_prompt(), {"context": "fixture"}),
    )

    assert result.answer == "ok"
    assert calls == 2
    assert sleeps == [1]
    assert provider.last_call_metadata["retries"] == 1
    assert provider.last_call_metadata["retry_history"][0]["request_id"] == "req_retry"


def test_openai_does_not_retry_account_quota_and_uses_native_schema() -> None:
    bodies: list[dict[str, object]] = []

    def transport(body: dict[str, object]) -> dict[str, object]:
        bodies.append(body)
        raise ProviderCallError(
            ProviderError(
                provider="openai",
                model="gpt-4.1-mini",
                status_code=429,
                error_code="insufficient_quota",
                error_type="insufficient_quota",
                category=ProviderErrorCategory.INSUFFICIENT_QUOTA,
                retryable=False,
                sanitized_message="Quota unavailable.",
            )
        )

    provider = OpenAIProvider(
        api_key="test-only-value",
        model="gpt-4.1-mini",
        transport=transport,
        retry_policy=ProviderRetryPolicy(max_attempts=2),
        sleeper=lambda _: pytest.fail("quota must not sleep or retry"),
    )

    with pytest.raises(ProviderCallError) as captured:
        provider.generate_structured(_prompt(), {"context": "fixture"})

    assert captured.value.error.blocked_external_account
    assert len(bodies) == 1
    assert bodies[0]["text"]["format"]["type"] == "json_schema"  # type: ignore[index]


def test_openai_repairs_invalid_schema_at_most_once() -> None:
    bodies: list[dict[str, object]] = []

    def transport(body: dict[str, object]) -> dict[str, object]:
        bodies.append(body)
        output = '{"wrong":"shape"}' if len(bodies) == 1 else '{"answer":"repaired"}'
        return {"id": f"resp_{len(bodies)}", "output_text": output}

    provider = OpenAIProvider(
        api_key="test-only-value",
        model="gpt-4.1-mini",
        transport=transport,
        retry_policy=ProviderRetryPolicy(max_attempts=1),
    )

    result = cast(
        _StructuredSample,
        provider.generate_structured(_prompt(), {"context": "original-context"}),
    )

    assert result.answer == "repaired"
    assert len(bodies) == 2
    assert provider.last_call_metadata["repaired"] is True
    assert provider.last_call_metadata["repair_attempted"] is True
    repair_input = json.dumps(bodies[1], ensure_ascii=False)
    assert "original-context" not in repair_input
    assert "wrong" in repair_input


def test_schema_repair_never_invokes_more_than_one_repair() -> None:
    calls = 0

    def repair(_: str, __: dict[str, object]) -> object:
        nonlocal calls
        calls += 1
        return {"still_wrong": True}

    with pytest.raises(SchemaRepairError):
        validate_with_single_repair({"wrong": True}, _StructuredSample, repair)

    assert calls == 1


def test_schema_repair_prompt_forbids_new_facts_and_missing_evidence() -> None:
    system, user = repair_instructions('{"answer":7}', _StructuredSample.model_json_schema())

    assert "Do not add facts" in system
    assert '"maximum_repairs": 1' in user
    assert '"add_facts": false' in user
    assert '"infer_missing_evidence": false' in user


def _gemini_response(
    *,
    parsed: object = None,
    text: str = "",
    finish_reason: str = "STOP",
    response_id: str = "gemini-safe-id",
) -> SimpleNamespace:
    return SimpleNamespace(
        parsed=parsed,
        text=text,
        response_id=response_id,
        candidates=[
            SimpleNamespace(
                finish_reason=finish_reason,
                safety_ratings=[],
            )
        ],
        usage_metadata=SimpleNamespace(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15,
        ),
    )


def test_gemini_uses_native_pydantic_schema_and_records_response_metadata() -> None:
    payloads: list[dict[str, object]] = []

    def transport(payload: dict[str, object]) -> object:
        payloads.append(payload)
        return _gemini_response(parsed={"answer": "ok"})

    provider = GeminiProvider(
        api_key="test-only-value",
        model="gemini-2.5-flash",
        transport=transport,
        retry_policy=ProviderRetryPolicy(max_attempts=1),
    )

    result = cast(
        _StructuredSample,
        provider.generate_structured(_prompt(), {"context": "fixture"}),
    )

    assert result.answer == "ok"
    response_schema = payloads[0]["config"]["response_json_schema"]  # type: ignore[index]
    assert response_schema["type"] == "object"  # type: ignore[index]
    assert "additionalProperties" not in json.dumps(response_schema)
    assert provider.last_call_metadata["request_id"] == "gemini-safe-id"
    assert provider.last_call_metadata["finish_reason"] == "STOP"
    assert provider.last_call_metadata["total_tokens"] == 15


def test_gemini_retries_transient_server_failure_then_repairs_once() -> None:
    calls = 0
    sleeps: list[float] = []

    class TransientError(RuntimeError):
        code = 503

    def transport(_: dict[str, object]) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TransientError("503 UNAVAILABLE")
        if calls == 2:
            return _gemini_response(text='{"wrong":"shape"}')
        return _gemini_response(parsed={"answer": "repaired"}, response_id="repair-safe-id")

    provider = GeminiProvider(
        api_key="test-only-value",
        model="gemini-2.5-flash",
        transport=transport,
        retry_policy=ProviderRetryPolicy(max_attempts=2, jitter_ratio=0),
        sleeper=sleeps.append,
    )

    result = cast(
        _StructuredSample,
        provider.generate_structured(_prompt(), {"context": "fixture"}),
    )

    assert result.answer == "repaired"
    assert calls == 3
    assert len(sleeps) == 1
    assert provider.last_call_metadata["repaired"] is True
    assert provider.last_call_metadata["repair_call_metadata"]["request_id"] == "repair-safe-id"


def test_gemini_safety_block_is_not_repaired_or_retried() -> None:
    calls = 0

    def transport(_: dict[str, object]) -> object:
        nonlocal calls
        calls += 1
        return _gemini_response(finish_reason="SAFETY")

    provider = GeminiProvider(
        api_key="test-only-value",
        model="gemini-2.5-flash",
        transport=transport,
        retry_policy=ProviderRetryPolicy(max_attempts=2),
        sleeper=lambda _: pytest.fail("safety block must not retry"),
    )

    with pytest.raises(ProviderCallError) as captured:
        provider.generate_structured(_prompt(), {"context": "fixture"})

    assert captured.value.error.category is ProviderErrorCategory.SAFETY_BLOCK
    assert calls == 1


def test_gemini_schema_normalizer_removes_only_unsupported_annotations() -> None:
    schema = gemini_response_json_schema(_StructuredSample)
    serialized = json.dumps(schema)

    assert schema["type"] == "object"
    assert "answer" in schema["properties"]
    assert "title" not in serialized
    assert "default" not in serialized
    assert "additionalProperties" not in serialized


def test_gemini_server_and_quota_failures_are_distinct() -> None:
    server = classify_gemini_error(
        RuntimeError("503 UNAVAILABLE: model overloaded"),
        model="gemini-2.5-flash",
        max_attempts=2,
    )
    quota = classify_gemini_error(
        RuntimeError("429 RESOURCE_EXHAUSTED: daily quota exceeded"),
        model="gemini-2.5-flash",
        max_attempts=2,
    )

    assert server.category is ProviderErrorCategory.MODEL_UNAVAILABLE
    assert server.retryable
    assert quota.category is ProviderErrorCategory.INSUFFICIENT_QUOTA
    assert not quota.retryable

    temporary = classify_gemini_error(
        RuntimeError(
            "429 RESOURCE_EXHAUSTED: free_tier_requests limit; please retry in 10.25s; "
            "check plan and billing details"
        ),
        model="gemini-2.5-flash",
        max_attempts=2,
    )
    assert temporary.category is ProviderErrorCategory.RATE_LIMIT
    assert temporary.retryable
    assert temporary.retry_after_seconds == 10.25


def test_provider_message_redacts_credentials_and_is_bounded() -> None:
    message = sanitize_provider_message(
        "Authorization: Bearer sk-example123 api_key=AIzaExample12345 " + "x" * 600
    )

    assert "sk-example123" not in message
    assert "AIzaExample12345" not in message
    assert "[REDACTED]" in message
    assert len(message) <= 500
