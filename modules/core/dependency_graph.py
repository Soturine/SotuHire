"""Deterministic dependency fingerprints for derived career artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DependencyFingerprint(BaseModel):
    """Immutable hash of named inputs used to derive one artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    digest: str
    inputs: dict[str, str] = Field(default_factory=dict)

    def stale_against(self, current: DependencyFingerprint) -> bool:
        """Return whether any canonical input changed."""
        return self.digest != current.digest


def fingerprint_dependencies(**inputs: Any) -> DependencyFingerprint:
    """Hash stable JSON representations without recording secret values in logs."""
    normalized = {
        name: _value_digest(value)
        for name, value in sorted(inputs.items())
    }
    digest = hashlib.sha256(_canonical_json(normalized).encode("utf-8")).hexdigest()
    return DependencyFingerprint(digest=digest, inputs=normalized)


def _value_digest(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


__all__ = ["DependencyFingerprint", "fingerprint_dependencies"]
