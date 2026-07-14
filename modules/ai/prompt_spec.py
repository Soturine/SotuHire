"""Prompt metadata used by structured AI calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from modules.ai.untrusted_content import UNTRUSTED_CONTENT_POLICY, wrap_untrusted_content


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
    context_policy: str = "minimum_necessary"
    evaluation_suite: str = "golden"
    golden_cases: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = (
        "invalid_json",
        "schema_mismatch",
        "unsupported_claim",
        "provider_error",
    )
    providers_tested: tuple[str, ...] = ("local",)
    last_benchmark: str = ""
    baseline_status: str = "pending"
    untrusted_fields: tuple[str, ...] = (
        "text",
        "resume_text",
        "job_text",
        "free_text",
        "selected_files",
        "repository_structure",
        "detected_signals",
        "evidence",
        "evidence_text",
        "context",
        "memory_context",
        "local_parser_draft",
    )

    @property
    def effective_system_prompt(self) -> str:
        """Return the system prompt with the common untrusted-data policy."""
        return f"{self.system_prompt}\n\n{UNTRUSTED_CONTENT_POLICY}"

    def render_user_prompt(self, payload: dict[str, object]) -> str:
        """Render the user template with stable placeholders."""
        bounded = dict(payload)
        for field in self.untrusted_fields:
            if field in bounded:
                bounded[field] = wrap_untrusted_content(bounded[field], label=field)
        return self.user_template.format_map(_SafeFormatDict(bounded))
