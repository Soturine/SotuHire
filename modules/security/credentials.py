"""Credential-shape detection and redaction shared by local security boundaries."""

from __future__ import annotations

import math
import re
from collections import Counter

_LEGACY_PROVIDER_PATTERNS = (
    re.compile(r"(?<![0-9A-Za-z_-])AIza[0-9A-Za-z_-]{20,}(?![0-9A-Za-z_-])"),
    re.compile(r"(?<![0-9A-Za-z_-])sk-(?:proj-)?[0-9A-Za-z_-]{20,}(?![0-9A-Za-z_-])"),
)
_MODERN_GEMINI_CANDIDATE = re.compile(
    r"(?<![0-9A-Za-z_-])AQ\.[0-9A-Za-z_-]{24,128}(?![0-9A-Za-z_-])"
)
_CREDENTIAL_CONTEXT = re.compile(
    r"(?i)(?:gemini|google|api[ _.-]?key|authorization|bearer|credential|secret|token)"
)


def looks_like_modern_gemini_key(value: str) -> bool:
    """Reject low-entropy prose while recognizing modern ``AQ.`` credentials."""
    candidate = str(value or "")
    if _MODERN_GEMINI_CANDIDATE.fullmatch(candidate) is None:
        return False
    payload = candidate[3:]
    if len(set(payload)) < 12:
        return False
    if not any(character.isalpha() for character in payload):
        return False
    if not any(character.isdigit() for character in payload):
        return False
    return _shannon_entropy(payload) >= 3.25


def contains_provider_secret(
    value: str,
    *,
    require_context_for_modern_gemini: bool = True,
) -> bool:
    """Return whether text contains a provider credential without exposing the value."""
    text = str(value or "")
    if any(pattern.search(text) for pattern in _LEGACY_PROVIDER_PATTERNS):
        return True
    for match in _MODERN_GEMINI_CANDIDATE.finditer(text):
        if not looks_like_modern_gemini_key(match.group(0)):
            continue
        if not require_context_for_modern_gemini or _has_credential_context(text, match.span()):
            return True
    return False


def redact_provider_secrets(value: object) -> str:
    """Redact provider credentials while leaving ordinary ``AQ.`` prose untouched."""
    text = str(value or "")
    for pattern in _LEGACY_PROVIDER_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    matches = [
        match
        for match in _MODERN_GEMINI_CANDIDATE.finditer(text)
        if looks_like_modern_gemini_key(match.group(0))
    ]
    for match in reversed(matches):
        text = f"{text[: match.start()]}[REDACTED]{text[match.end() :]}"
    return text


def _has_credential_context(text: str, span: tuple[int, int]) -> bool:
    start, end = span
    window = text[max(0, start - 96) : min(len(text), end + 96)]
    return _CREDENTIAL_CONTEXT.search(window) is not None


def _shannon_entropy(value: str) -> float:
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


__all__ = [
    "contains_provider_secret",
    "looks_like_modern_gemini_key",
    "redact_provider_secrets",
]
