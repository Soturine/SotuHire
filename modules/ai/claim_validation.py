"""Deterministic post-schema checks for explicitly forbidden claims."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from modules.matching.requirement_matcher import detect_professional_credentials


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


# Degrees a model tends to invent. Each normalized pattern maps to the label shown to the user.
_DEGREE_PATTERNS = (
    (r"pos doutorado|pos doc|postdoc", "pós-doutorado"),
    (r"doutorado|doutora|doutor em|phd|ph d", "doutorado"),
    (r"mestrado|mestre em|mestra em|master of", "mestrado"),
    (r"mba", "MBA"),
    (r"especializacao|pos graduacao|lato sensu", "especialização/pós-graduação"),
)


def credential_claims(text: str) -> list[str]:
    """Professional registrations and graduate degrees that ``text`` asserts, as display labels."""
    folded = _normalize(_fold_accents(text))
    found = [credential.code for credential in detect_professional_credentials(text)]
    for pattern, label in _DEGREE_PATTERNS:  # most specific first; a match consumes its span
        regex = re.compile(rf"(?<![a-z0-9])(?:{pattern})(?![a-z0-9])")
        if regex.search(folded):
            if label not in found:
                found.append(label)
            folded = regex.sub(" ", folded)
    return found


def unsupported_credential_claims(text: str, evidence_texts: list[str]) -> list[str]:
    """Credentials asserted by ``text`` that no evidence text asserts.

    Deterministic and conservative: it only knows registrations and graduate degrees, the claims
    whose invention does the most harm on a resume. Absence from this list is not proof that the
    text is supported.
    """
    supported = set(credential_claims("\n".join(evidence_texts)))
    return [claim for claim in credential_claims(text) if claim not in supported]


def _fold_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    )


__all__ = [
    "ClaimValidationResult",
    "credential_claims",
    "unsupported_credential_claims",
    "validate_forbidden_claims",
]
