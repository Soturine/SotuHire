"""Exceptions raised by structured AI helpers."""

from __future__ import annotations


class AIJsonError(ValueError):
    """Base error for AI JSON parsing and validation failures."""


class AIJsonParseError(AIJsonError):
    """Raised when a provider response cannot be parsed as JSON."""


class AISchemaValidationError(AIJsonError):
    """Raised when parsed JSON does not match the expected schema."""
