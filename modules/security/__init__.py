"""Security primitives shared by SotuHire localhost services."""

from .credentials import (
    contains_provider_secret,
    looks_like_modern_gemini_key,
    redact_provider_secrets,
)
from .local_auth import (
    LocalAuthManager,
    PairingChallenge,
    PairingError,
    SessionCredentials,
)
from .request_limits import LocalRateLimiter, RequestLimitError, RequestPolicy

__all__ = [
    "LocalAuthManager",
    "LocalRateLimiter",
    "PairingChallenge",
    "PairingError",
    "RequestLimitError",
    "RequestPolicy",
    "SessionCredentials",
    "contains_provider_secret",
    "looks_like_modern_gemini_key",
    "redact_provider_secrets",
]
