"""Small registry for versioned AI prompts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from pydantic import BaseModel

from modules.ai.prompt_spec import PromptSpec


class PromptRegistryError(LookupError):
    """Raised when a prompt cannot be resolved."""


class PromptRegistry:
    """In-memory registry for prompt specs keyed by prompt id and version."""

    def __init__(self, specs: Iterable[PromptSpec] | None = None) -> None:
        self._specs: dict[str, dict[str, PromptSpec]] = defaultdict(dict)
        for spec in specs or []:
            self.register(spec)

    def register(self, spec: PromptSpec) -> None:
        """Register or replace a prompt spec by id and version."""
        self._specs[spec.prompt_id][spec.version] = spec

    def get(self, prompt_id: str, version: str | None = None) -> PromptSpec:
        """Return a prompt by id and optional version."""
        versions = self._specs.get(prompt_id)
        if not versions:
            raise PromptRegistryError(f"Prompt not registered: {prompt_id}")
        if version:
            spec = versions.get(version)
            if not spec:
                raise PromptRegistryError(f"Prompt not registered: {prompt_id}@{version}")
            return spec
        return versions[sorted(versions)[-1]]

    def render_user_prompt(
        self,
        prompt_id: str,
        payload: dict[str, object],
        version: str | None = None,
    ) -> str:
        """Render a registered user prompt template."""
        return self.get(prompt_id, version).render_user_prompt(payload)

    def output_schema(
        self,
        prompt_id: str,
        version: str | None = None,
    ) -> type[BaseModel]:
        """Return the expected Pydantic schema for a prompt."""
        return self.get(prompt_id, version).output_schema

    def list_prompt_ids(self) -> list[str]:
        """Return registered prompt ids in stable order."""
        return sorted(self._specs)
