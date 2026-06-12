"""Schemas for safe resume tailoring."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TailoredResumeSection(BaseModel):
    """A single resume section rewritten with evidence tracking."""

    model_config = ConfigDict(extra="forbid")

    section_name: str = Field(min_length=1)
    original_text: str
    tailored_text: str
    reason_for_change: str = Field(min_length=1)
    evidence_source: str = Field(min_length=1)
    invented_information: Literal[False] = False


class ResumeTailorOutput(BaseModel):
    """Structured result for a tailored resume draft."""

    model_config = ConfigDict(extra="forbid")

    target_role: str = Field(min_length=1)
    target_company: str | None = None
    section_order: list[str] = Field(default_factory=list)
    tailored_sections: list[TailoredResumeSection] = Field(default_factory=list)
    professional_summary: str = ""
    improved_bullets: list[str] = Field(default_factory=list)
    keywords_added: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def has_invented_information(self) -> bool:
        """Return True if any section was flagged as invented."""
        return any(section.invented_information for section in self.tailored_sections)

    def is_safe_to_export(self) -> bool:
        """Return True when the output can be exported after user review."""
        return not self.has_invented_information()
