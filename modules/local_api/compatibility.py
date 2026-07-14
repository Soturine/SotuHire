"""Version and capability negotiation for the browser extension bridge."""

from __future__ import annotations

APP_VERSION = "1.9.7"
COMPANION_VERSION = "1.9.7"
API_VERSION = "v1"
MIN_SUPPORTED_EXTENSION_VERSION = "0.9.1"
MAX_TESTED_EXTENSION_VERSION = "0.9.3"
MIN_SUPPORTED_COMPANION_VERSION = "1.9.5"
EXTENSION_CAPABILITIES = [
    "capture.job",
    "capture.public_exam",
    "capture.github",
    "capture.snapshot",
    "queue.retry",
    "queue.export_import",
    "jobposting.jsonld",
    "ai.own_key",
    "ai.sotuhire_provider",
    "profile.review_candidates",
]


def compatible_extension(version: str) -> tuple[bool, list[str]]:
    """Return compatibility and user-facing warnings for one extension version."""
    parsed = _version_tuple(version)
    minimum = _version_tuple(MIN_SUPPORTED_EXTENSION_VERSION)
    maximum = _version_tuple(MAX_TESTED_EXTENSION_VERSION)
    if parsed < minimum:
        return False, [f"Extensão {version} é anterior ao mínimo suportado."]
    if parsed > maximum:
        return True, [f"Extensão {version} é mais nova que a versão testada."]
    return True, []


def _version_tuple(value: str) -> tuple[int, int, int]:
    parts = []
    for item in value.split(".")[:3]:
        digits = "".join(character for character in item if character.isdigit())
        parts.append(int(digits or 0))
    return tuple([*parts, 0, 0, 0][:3])  # type: ignore[return-value]
