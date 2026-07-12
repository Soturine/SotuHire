"""Runtime configuration for the local frontend API."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

API_VERSION = "1.9.5"
DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "https://soturine.github.io",
)


@dataclass(frozen=True)
class ApiSettings:
    """Small env-backed settings object without adding pydantic-settings."""

    version: str = API_VERSION
    host: str = "127.0.0.1"
    port: int = 8787
    allowed_origins: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_ORIGINS))

    @classmethod
    def from_env(cls) -> ApiSettings:
        """Build settings from optional SOTUHIRE_API_* variables."""
        origins = _split_csv(os.getenv("SOTUHIRE_API_ALLOWED_ORIGINS", ""))
        raw_port = os.getenv("SOTUHIRE_API_PORT", "").strip()
        return cls(
            host=os.getenv("SOTUHIRE_API_HOST", "127.0.0.1").strip() or "127.0.0.1",
            port=int(raw_port) if raw_port.isdigit() else 8787,
            allowed_origins=origins or list(DEFAULT_ALLOWED_ORIGINS),
        )


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
