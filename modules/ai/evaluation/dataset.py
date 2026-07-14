"""Versioned golden-case contracts and loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GoldenCase(BaseModel):
    """One fictitious, evidence-labelled evaluation case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    task_id: str
    domain: str
    career_moment: str
    language: str = "pt-BR"
    input: dict[str, Any]
    expected_fields: dict[str, Any]
    allowed_variants: dict[str, list[Any]] = Field(default_factory=dict)
    forbidden_claims: list[str] = Field(default_factory=list)
    required_evidence_refs: list[str] = Field(default_factory=list)
    expected_missing_information: list[str] = Field(default_factory=list)
    expected_confidence_range: tuple[float, float]
    expected_warnings: list[str] = Field(default_factory=list)
    privacy_level: Literal["public_fictitious", "synthetic_sensitive"] = "public_fictitious"
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_confidence_range(self) -> GoldenCase:
        low, high = self.expected_confidence_range
        if not 0 <= low <= high <= 1:
            raise ValueError("expected_confidence_range must be between 0 and 1")
        return self


def load_golden_case(path: str | Path) -> GoldenCase:
    """Load and validate one JSON golden case."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return GoldenCase.model_validate(payload)


def iter_golden_cases(root: str | Path = "tests/golden") -> list[GoldenCase]:
    """Return all versioned cases in stable path order."""
    base = Path(root)
    return [load_golden_case(path) for path in sorted(base.rglob("*.json"))]


__all__ = ["GoldenCase", "iter_golden_cases", "load_golden_case"]
