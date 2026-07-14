"""Deterministic post-schema checks for explicitly forbidden claims."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClaimValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    matched_forbidden_claims: list[str] = Field(default_factory=list)
    unsupported_paths: list[str] = Field(default_factory=list)


def validate_forbidden_claims(
    output: BaseModel | dict[str, Any], forbidden_claims: list[str]
) -> ClaimValidationResult:
    """Find forbidden terms and claims whose adjacent evidence collection is empty."""
    payload = output.model_dump(mode="json") if isinstance(output, BaseModel) else output
    text = _normalize(" ".join(_strings(payload)))
    matched = [claim for claim in forbidden_claims if _normalize(claim) in text]
    unsupported = _unsupported_paths(payload)
    return ClaimValidationResult(
        valid=not matched,
        matched_forbidden_claims=matched,
        unsupported_paths=unsupported,
    )


def _unsupported_paths(value: Any, path: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        claim = value.get("claim") or value.get("statement")
        evidence = value.get("evidence") or value.get("evidence_refs")
        if isinstance(claim, str) and not evidence:
            paths.append(path or "$")
        for key, nested in value.items():
            child = f"{path}.{key}" if path else key
            paths.extend(_unsupported_paths(nested, child))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_unsupported_paths(nested, f"{path}[{index}]"))
    return paths


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _strings(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in _strings(nested)]
    return []


def _normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


__all__ = ["ClaimValidationResult", "validate_forbidden_claims"]
