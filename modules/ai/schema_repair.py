"""One-shot structured-output repair without access to original user context."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from modules.ai.exceptions import AIJsonError
from modules.ai.json_guard import validate_ai_json
from modules.ai.provider_errors import sanitize_provider_message

T = TypeVar("T", bound=BaseModel)
RepairCallable = Callable[[str, dict[str, Any]], object]


@dataclass(frozen=True)
class SchemaRepairResult(Generic[T]):
    """Validated structured output and auditable repair metadata."""

    data: T
    repaired: bool
    repair_reason: str = ""


class SchemaRepairError(ValueError):
    """Raised after the original output and the single repair are both invalid."""

    def __init__(self, original_reason: str, repair_reason: str) -> None:
        self.original_reason = sanitize_provider_message(original_reason)
        self.repair_reason = sanitize_provider_message(repair_reason)
        super().__init__(
            "Structured output remained invalid after one repair: " + self.repair_reason
        )


def validate_with_single_repair(
    raw_output: object,
    schema: type[T],
    repair: RepairCallable,
) -> SchemaRepairResult[T]:
    """Validate once, invoke exactly one constrained repair, then validate once more."""
    try:
        return SchemaRepairResult(data=_validate(raw_output, schema), repaired=False)
    except (AIJsonError, TypeError, ValueError) as original_error:
        original_reason = _reason(original_error)
    repaired_output = repair(_serialized_output(raw_output), schema.model_json_schema())
    try:
        data = _validate(repaired_output, schema)
    except (AIJsonError, TypeError, ValueError) as repair_error:
        raise SchemaRepairError(original_reason, _reason(repair_error)) from repair_error
    return SchemaRepairResult(data=data, repaired=True, repair_reason=original_reason)


def repair_instructions(invalid_response: str, schema: dict[str, Any]) -> tuple[str, str]:
    """Build a repair-only prompt that contains no original prompt, evidence or credentials."""
    system = (
        "Repair only the JSON structure and types. Do not add facts, evidence, claims or "
        "content that is absent from the invalid response. Preserve uncertainty and empty "
        "values. Return only JSON matching the supplied schema."
    )
    user = json.dumps(
        {
            "invalid_response": invalid_response,
            "output_schema": schema,
            "constraints": {
                "maximum_repairs": 1,
                "add_facts": False,
                "infer_missing_evidence": False,
            },
        },
        ensure_ascii=False,
    )
    return system, user


def _validate(raw_output: object, schema: type[T]) -> T:
    if isinstance(raw_output, schema):
        return raw_output
    if isinstance(raw_output, BaseModel):
        return schema.model_validate(raw_output.model_dump(mode="json"))
    return validate_ai_json(raw_output, schema).data  # type: ignore[arg-type]


def _serialized_output(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[:200_000]
    if isinstance(value, str):
        return value[:200_000]
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    try:
        return json.dumps(value, ensure_ascii=False, default=str)[:200_000]
    except (TypeError, ValueError):
        return sanitize_provider_message(value, limit=200_000)


def _reason(error: BaseException) -> str:
    return sanitize_provider_message(f"{type(error).__name__}: {error}")


__all__ = [
    "SchemaRepairError",
    "SchemaRepairResult",
    "repair_instructions",
    "validate_with_single_repair",
]
