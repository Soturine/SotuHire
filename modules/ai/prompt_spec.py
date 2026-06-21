"""Prompt metadata used by structured AI calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


class _SafeFormatDict(dict[str, Any]):
    """Leave unknown template keys visible instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(frozen=True)
class PromptSpec:
    """Versioned prompt contract with its expected structured output schema."""

    prompt_id: str
    version: str
    system_prompt: str
    user_template: str
    output_schema: type[BaseModel]
    temperature: float = 0.1
    mode: str = "structured_extraction"
    max_retries: int = 1

    def render_user_prompt(self, payload: dict[str, object]) -> str:
        """Render the user template with stable placeholders."""
        return self.user_template.format_map(_SafeFormatDict(payload))
