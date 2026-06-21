"""Guardrails for AI responses that must be valid JSON."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from modules.ai.exceptions import AIJsonParseError, AISchemaValidationError

T = TypeVar("T", bound=BaseModel)
FENCE_PATTERN = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)


@dataclass(frozen=True)
class JsonGuardResult(Generic[T]):
    """Validated schema plus confidence metadata discovered in the payload."""

    data: T
    low_confidence_fields: list[str]


def clean_json_text(raw_text: str) -> str:
    """Remove common Markdown wrappers from provider JSON responses."""
    text = (raw_text or "").strip()
    match = FENCE_PATTERN.match(text)
    if match:
        return match.group(1).strip()
    return text


def parse_json(raw_payload: str | bytes | dict[str, Any] | list[Any]) -> Any:
    """Parse provider output as JSON while accepting already parsed payloads."""
    if isinstance(raw_payload, dict | list):
        return raw_payload
    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8", errors="replace")
    cleaned = clean_json_text(raw_payload)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIJsonParseError(f"Invalid AI JSON response: {exc.msg}") from exc


def validate_ai_json(
    raw_payload: str | bytes | dict[str, Any] | list[Any],
    schema: type[T],
    *,
    low_confidence_threshold: float = 0.7,
) -> JsonGuardResult[T]:
    """Parse and validate a provider response against a Pydantic schema."""
    parsed = parse_json(raw_payload)
    try:
        data = schema.model_validate(parsed)
    except ValidationError as exc:
        raise AISchemaValidationError(f"AI JSON does not match {schema.__name__}") from exc
    return JsonGuardResult(
        data=data,
        low_confidence_fields=collect_low_confidence_fields(
            data.model_dump(mode="json"),
            threshold=low_confidence_threshold,
        ),
    )


def collect_low_confidence_fields(
    payload: Any,
    *,
    threshold: float = 0.7,
    path: str = "",
) -> list[str]:
    """Return JSON paths whose local confidence is below the threshold."""
    fields: list[str] = []
    if isinstance(payload, dict):
        confidence = payload.get("confidence")
        if isinstance(confidence, int | float) and confidence < threshold:
            fields.append(path or "$")
        for key, value in payload.items():
            child_path = f"{path}.{key}" if path else key
            fields.extend(
                collect_low_confidence_fields(value, threshold=threshold, path=child_path)
            )
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            fields.extend(
                collect_low_confidence_fields(value, threshold=threshold, path=child_path)
            )
    return list(dict.fromkeys(fields))
