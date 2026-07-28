from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

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
from modules.ai.providers.openai_provider import OpenAIProvider
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
    parsed = parse_retry_after((now + timedelta(seconds=10)).strftime("%a, %d %b %Y %H:%M:%S GMT"), now=now)
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

    result = provider.generate_structured(_prompt(), {"context": "fixture"})

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


def test_provider_message_redacts_credentials_and_is_bounded() -> None:
    message = sanitize_provider_message(
        "Authorization: Bearer sk-example-secret-token api_key=AIzaExampleSecretValue " + "x" * 600
    )

    assert "sk-example" not in message
    assert "AIzaExample" not in message
    assert "[REDACTED]" in message
    assert len(message) <= 500
