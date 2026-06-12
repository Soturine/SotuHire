"""Schemas for safe resume tailoring."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TailoredResumeSection(BaseModel):
    """A single resume section rewritten with evidence tracking."""

    section_name: str
    original_text: str
    tailored_text: str
    reason_for_change: str
    evidence_source: str
    invented_information: bool = False


class ResumeTailorOutput(BaseModel):
    """Structured result for a tailored resume draft."""

    target_role: str
    target_company: str | None = None
    section_order: list[str] = Field(default_factory=list)
    tailored_sections: list[TailoredResumeSection] = Field(default_factory=list)
    keywords_added: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def has_invented_information(self) -> bool:
        """Return True if any section was flagged as invented."""
        return any(section.invented_information for section in self.tailored_sections)

    def is_safe_to_export(self) -> bool:
        """Return True when the output can be exported after user review."""
        return not self.has_invented_information()
