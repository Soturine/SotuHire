"""Sanitized provider errors, retry policy and external-account diagnostics."""

from __future__ import annotations

import json
import random
import re
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from modules.ai.exceptions import ProviderUnavailableError
from modules.security.credentials import redact_provider_secrets


class ProviderErrorCategory(StrEnum):
    """Stable error categories shared by providers, traces, API and benchmarks."""

    AUTHENTICATION = "AUTHENTICATION"
    PERMISSION = "PERMISSION"
    INSUFFICIENT_QUOTA = "INSUFFICIENT_QUOTA"
    RATE_LIMIT = "RATE_LIMIT"
    BILLING_REQUIRED = "BILLING_REQUIRED"
    PROJECT_LIMIT = "PROJECT_LIMIT"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    SAFETY_BLOCK = "SAFETY_BLOCK"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    TRUNCATED_RESPONSE = "TRUNCATED_RESPONSE"
    TIMEOUT = "TIMEOUT"
    NETWORK = "NETWORK"
    PROVIDER_INTERNAL = "PROVIDER_INTERNAL"
    UNKNOWN = "UNKNOWN"


class ProviderError(BaseModel):
    """Secret-free metadata for one failed provider attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    model: str
    status_code: int | None = None
    error_code: str = ""
    error_type: str = ""
    category: ProviderErrorCategory = ProviderErrorCategory.UNKNOWN
    retryable: bool = False
    retry_after_seconds: float | None = Field(default=None, ge=0)
    request_id: str = ""
    sanitized_message: str = ""
    attempt: int = Field(default=1, ge=1)
    max_attempts: int = Field(default=1, ge=1)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def blocked_external_account(self) -> bool:
        """Return whether local code cannot validate this account until its state changes."""
        return self.category in {
            ProviderErrorCategory.INSUFFICIENT_QUOTA,
            ProviderErrorCategory.BILLING_REQUIRED,
            ProviderErrorCategory.PROJECT_LIMIT,
            ProviderErrorCategory.AUTHENTICATION,
            ProviderErrorCategory.PERMISSION,
        }


class ProviderCallError(ProviderUnavailableError):
    """Exception carrying a sanitized, machine-readable provider error."""

    def __init__(self, error: ProviderError) -> None:
        self.error = error
        super().__init__(
            f"{error.provider}/{error.model}: {error.category.value}"
            + (f" (HTTP {error.status_code})" if error.status_code else "")
            + (f" — {error.sanitized_message}" if error.sanitized_message else "")
        )


class ProviderRetryPolicy(BaseModel):
    """Small retry budget that avoids request storms."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_attempts: int = Field(default=2, ge=1, le=3)
    base_delay_seconds: float = Field(default=0.5, ge=0, le=30)
    max_delay_seconds: float = Field(default=30.0, ge=0, le=120)
    jitter_ratio: float = Field(default=0.2, ge=0, le=1)

    def delay_seconds(
        self,
        error: ProviderError,
        *,
        random_value: Callable[[], float] = random.random,
    ) -> float:
        """Compute bounded exponential delay, respecting provider Retry-After."""
        if error.retry_after_seconds is not None:
            base = min(error.retry_after_seconds, self.max_delay_seconds)
        else:
            base = min(
                self.base_delay_seconds * (2 ** max(0, error.attempt - 1)),
                self.max_delay_seconds,
            )
        jitter = base * self.jitter_ratio * max(0.0, min(1.0, random_value()))
        return min(self.max_delay_seconds, base + jitter)


_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
)


def sanitize_provider_message(value: object, *, limit: int = 500) -> str:
    """Return one bounded line with credential-shaped values redacted."""
    message = " ".join(str(value or "").split())
    for pattern in _SECRET_PATTERNS:
        message = pattern.sub(
            lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED]",
            message,
        )
    message = redact_provider_secrets(message)
    return message[:limit]


def classify_openai_error(
    *,
    model: str,
    status_code: int | None,
    headers: object = None,
    body: object = None,
    exception: BaseException | None = None,
    attempt: int = 1,
    max_attempts: int = 1,
) -> ProviderError:
    """Classify OpenAI HTTP/network errors without retaining a response body."""
    payload = _error_payload(body)
    error_code = _text(payload.get("code"))
    error_type = _text(payload.get("type")) or (
        type(exception).__name__ if exception is not None else ""
    )
    message = _text(payload.get("message")) or sanitize_provider_message(exception)
    lower = " ".join([error_code, error_type, message]).casefold()
    retry_after = parse_retry_after(_header(headers, "retry-after"))
    category, retryable = _openai_category(status_code, lower, retry_after)
    return ProviderError(
        provider="openai",
        model=model,
        status_code=status_code,
        error_code=error_code,
        error_type=error_type,
        category=category,
        retryable=retryable,
        retry_after_seconds=retry_after,
        request_id=_request_id(headers),
        sanitized_message=sanitize_provider_message(message or category.value),
        attempt=attempt,
        max_attempts=max_attempts,
    )


def classify_gemini_error(
    exception: BaseException,
    *,
    model: str,
    attempt: int = 1,
    max_attempts: int = 1,
) -> ProviderError:
    """Classify google-genai exceptions through stable public attributes."""
    status = _integer(
        getattr(exception, "code", None)
        or getattr(exception, "status_code", None)
        or getattr(exception, "status", None)
    )
    raw_message = sanitize_provider_message(exception)
    lower = raw_message.casefold()
    retry_after = parse_retry_after(
        getattr(exception, "retry_after", None)
        or _header(getattr(exception, "headers", None), "retry-after")
    )
    retry_after = retry_after if retry_after is not None else _retry_after_from_message(raw_message)
    if status in {401} or "unauthenticated" in lower or "api key not valid" in lower:
        category, retryable = ProviderErrorCategory.AUTHENTICATION, False
    elif status == 403 or "permission_denied" in lower:
        category, retryable = ProviderErrorCategory.PERMISSION, False
    elif status == 404 or "not_found" in lower:
        category, retryable = ProviderErrorCategory.MODEL_NOT_FOUND, False
    elif status == 429 or "resource_exhausted" in lower:
        if retry_after is not None:
            category, retryable = ProviderErrorCategory.RATE_LIMIT, True
        elif any(
            token in lower
            for token in ("billing_not_active", "billing is not active", "enable billing")
        ):
            category, retryable = ProviderErrorCategory.BILLING_REQUIRED, False
        elif any(token in lower for token in ("per day", "daily", "quota")) and retry_after is None:
            category, retryable = ProviderErrorCategory.INSUFFICIENT_QUOTA, False
        else:
            category, retryable = ProviderErrorCategory.RATE_LIMIT, True
    elif status in {408, 504} or "timeout" in lower or "deadline_exceeded" in lower:
        category, retryable = ProviderErrorCategory.TIMEOUT, True
    elif status in {500, 502, 503} or "unavailable" in lower or "servererror" in lower:
        category, retryable = ProviderErrorCategory.MODEL_UNAVAILABLE, True
    elif status == 400 or "invalid_argument" in lower:
        category, retryable = ProviderErrorCategory.INVALID_REQUEST, False
    elif "safety" in lower or "blocked" in lower:
        category, retryable = ProviderErrorCategory.SAFETY_BLOCK, False
    else:
        category, retryable = ProviderErrorCategory.UNKNOWN, False
    return ProviderError(
        provider="gemini",
        model=model,
        status_code=status,
        error_code=_text(getattr(exception, "code", "")),
        error_type=type(exception).__name__,
        category=category,
        retryable=retryable,
        retry_after_seconds=retry_after,
        request_id=_text(
            getattr(exception, "request_id", "")
            or _header(getattr(exception, "headers", None), "x-request-id")
        ),
        sanitized_message=raw_message or category.value,
        attempt=attempt,
        max_attempts=max_attempts,
    )


def parse_retry_after(value: object, *, now: datetime | None = None) -> float | None:
    """Parse Retry-After seconds or HTTP date into a non-negative delay."""
    if value is None or value == "":
        return None
    try:
        return max(0.0, float(str(value).strip()))
    except ValueError:
        pass
    try:
        target = parsedate_to_datetime(str(value))
        current = now or datetime.now(UTC)
        if target.tzinfo is None:
            target = target.replace(tzinfo=UTC)
        return max(0.0, (target - current).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def _openai_category(
    status_code: int | None, lower: str, retry_after: float | None
) -> tuple[ProviderErrorCategory, bool]:
    if status_code == 401:
        return ProviderErrorCategory.AUTHENTICATION, False
    if status_code == 403:
        return ProviderErrorCategory.PERMISSION, False
    if status_code == 404:
        return ProviderErrorCategory.MODEL_NOT_FOUND, False
    if status_code == 429:
        if "insufficient_quota" in lower or "exceeded your current quota" in lower:
            return ProviderErrorCategory.INSUFFICIENT_QUOTA, False
        if any(token in lower for token in ("billing_not_active", "billing", "payment required")):
            return ProviderErrorCategory.BILLING_REQUIRED, False
        if any(
            token in lower for token in ("project_limit", "organization_limit", "project quota")
        ):
            return ProviderErrorCategory.PROJECT_LIMIT, False
        if "rate_limit_exceeded" in lower or retry_after is not None:
            return ProviderErrorCategory.RATE_LIMIT, True
        return ProviderErrorCategory.RATE_LIMIT, True
    if status_code in {408, 504}:
        return ProviderErrorCategory.TIMEOUT, True
    if status_code is not None and status_code >= 500:
        return ProviderErrorCategory.PROVIDER_INTERNAL, True
    if status_code == 400:
        return ProviderErrorCategory.INVALID_REQUEST, False
    if "timeout" in lower:
        return ProviderErrorCategory.TIMEOUT, True
    if "network" in lower or "urlerror" in lower:
        return ProviderErrorCategory.NETWORK, True
    return ProviderErrorCategory.UNKNOWN, False


def _error_payload(body: object) -> dict[str, Any]:
    value = body
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {"message": sanitize_provider_message(value)}
    if not isinstance(value, dict):
        return {}
    nested = value.get("error", value)
    return nested if isinstance(nested, dict) else {}


def _header(headers: object, name: str) -> str:
    if headers is None:
        return ""
    if hasattr(headers, "get"):
        for candidate in (name, name.lower(), name.upper(), name.title()):
            value = headers.get(candidate)  # type: ignore[union-attr]
            if value not in (None, ""):
                return str(value)
    return ""


def _request_id(headers: object) -> str:
    for name in ("x-request-id", "openai-request-id", "request-id"):
        value = _header(headers, name)
        if value:
            return sanitize_provider_message(value, limit=160)
    return ""


def _text(value: object) -> str:
    return sanitize_provider_message(value)


def _integer(value: object) -> int | None:
    if not isinstance(value, str | int | float | bool):
        return None
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _retry_after_from_message(message: str) -> float | None:
    match = re.search(r"(?i)(?:please\s+)?retry\s+in\s+([0-9]+(?:\.[0-9]+)?)\s*s", message)
    return float(match.group(1)) if match else None


__all__ = [
    "ProviderCallError",
    "ProviderError",
    "ProviderErrorCategory",
    "ProviderRetryPolicy",
    "classify_gemini_error",
    "classify_openai_error",
    "parse_retry_after",
    "sanitize_provider_message",
]
