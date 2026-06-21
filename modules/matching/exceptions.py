"""Exceptions for Match Engine 2."""

from __future__ import annotations


class MatchEngineError(RuntimeError):
    """Base error for Match Engine 2 failures."""


class MatchInputError(MatchEngineError, ValueError):
    """Raised when matching input cannot be normalized safely."""
