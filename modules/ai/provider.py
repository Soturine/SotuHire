"""Backward-compatible import for the structured provider contract."""

from modules.ai.providers.base import AIProvider, ProviderUnavailableError

__all__ = ["AIProvider", "ProviderUnavailableError"]
