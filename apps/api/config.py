"""Runtime configuration for the local frontend API."""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

API_VERSION = "1.9.9"
DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
)
DEFAULT_ALLOWED_HOSTS = ("127.0.0.1", "localhost", "::1")


@dataclass(frozen=True)
class ApiSettings:
    """Small env-backed settings object without adding pydantic-settings."""

    version: str = API_VERSION
    host: str = "127.0.0.1"
    port: int = 8787
    allowed_origins: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_ORIGINS))
    allowed_hosts: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_HOSTS))
    installation_token: str = ""
    auth_path: Path = Path("data/security/local-auth.json")
    max_body_bytes: int = 12 * 1024 * 1024
    max_batch_items: int = 100
    max_json_depth: int = 16
    request_timeout_seconds: float = 30.0
    rate_limit_requests: int = 120
    rate_limit_window_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> ApiSettings:
        """Build settings from optional SOTUHIRE_API_* variables."""
        origins = _split_csv(os.getenv("SOTUHIRE_API_ALLOWED_ORIGINS", ""))
        raw_port = os.getenv("SOTUHIRE_API_PORT", "").strip()
        allow_remote = _as_bool(os.getenv("SOTUHIRE_API_ALLOW_REMOTE_ORIGINS", ""))
        resolved_origins = origins or list(DEFAULT_ALLOWED_ORIGINS)
        remote_origins = [origin for origin in resolved_origins if not _is_loopback_origin(origin)]
        if remote_origins and not allow_remote:
            raise ValueError(
                "Origins remotas exigem SOTUHIRE_API_ALLOW_REMOTE_ORIGINS=1 explícito."
            )
        if remote_origins:
            warnings.warn(
                "A API local foi configurada com origin remota; revise o risco de exposição.",
                RuntimeWarning,
                stacklevel=2,
            )
        data_dir = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        host = os.getenv("SOTUHIRE_API_HOST", "127.0.0.1").strip() or "127.0.0.1"
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("A API local deve permanecer vinculada a um endereço loopback.")
        return cls(
            host=host,
            port=int(raw_port) if raw_port.isdigit() else 8787,
            allowed_origins=resolved_origins,
            allowed_hosts=_split_csv(os.getenv("SOTUHIRE_API_ALLOWED_HOSTS", ""))
            or list(DEFAULT_ALLOWED_HOSTS),
            installation_token=os.getenv("SOTUHIRE_LOCAL_API_TOKEN", "").strip(),
            auth_path=data_dir / "security" / "local-auth.json",
        )


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _as_bool(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _is_loopback_origin(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "127.0.0.1",
        "localhost",
        "::1",
    }
