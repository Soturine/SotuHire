"""Canonical professional document shared by editor, preview, snapshots and exports."""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.application_lab.models import MasterResume, ResumeVariant
from modules.evidence import EvidenceReviewStatus

ResumeDocument = MasterResume | ResumeVariant


class CanonicalDocumentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entry_id: str
    entry_type: str
    title: str = ""
    subtitle: str = ""
    content: str = ""
    start_date: str = ""
    end_date: str = ""
    source_profile_item_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    review_status: EvidenceReviewStatus
    confirmed_by_user: bool


class CanonicalDocumentSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str
    section_type: str
    title: str
    content: str = ""
    entries: tuple[CanonicalDocumentEntry, ...] = ()


class CanonicalProfessionalDocument(BaseModel):
    """Versioned content model; renderers never read ad-hoc fields from UI state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    document_kind: Literal["master_resume", "resume_variant"]
    master_resume_id: str
    resume_variant_id: str = ""
    version: int = Field(default=1, ge=1)
    title: str
    target_role: str = ""
    summary: str = ""
    sections: tuple[CanonicalDocumentSection, ...] = ()
    source_profile_item_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    content_hash: str = ""

    @model_validator(mode="after")
    def add_content_hash(self) -> CanonicalProfessionalDocument:
        if self.content_hash:
            return self
        payload = self.model_dump(mode="json", exclude={"content_hash"})
        digest = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        object.__setattr__(self, "content_hash", digest)
        return self

    def plain_text(self) -> str:
        lines = [self.title, self.target_role, self.summary]
        for section in self.sections:
            lines.extend([section.title, section.content])
            for entry in section.entries:
                lines.extend([entry.title, entry.subtitle, entry.content])
        return "\n".join(value.strip() for value in lines if value.strip())


def canonical_document(resume: ResumeDocument) -> CanonicalProfessionalDocument:
    """Freeze the enabled resume state used by every downstream representation."""
    is_variant = isinstance(resume, ResumeVariant)
    sections = tuple(
        CanonicalDocumentSection(
            section_id=section.section_id,
            section_type=section.section_type,
            title=section.title,
            content=section.content,
            entries=tuple(
                CanonicalDocumentEntry(
                    entry_id=entry.entry_id,
                    entry_type=entry.entry_type,
                    title=entry.title,
                    subtitle=entry.subtitle,
                    content=entry.content,
                    start_date=entry.start_date,
                    end_date=entry.end_date,
                    source_profile_item_ids=tuple(entry.source_profile_item_ids),
                    source_refs=tuple(entry.source_refs),
                    review_status=entry.review_status,
                    confirmed_by_user=entry.confirmed_by_user,
                )
                for entry in sorted(section.entries, key=lambda value: value.position)
                if entry.enabled
            ),
        )
        for section in sorted(resume.sections, key=lambda value: value.position)
        if section.enabled
    )
    source_ref_values: list[str] = [] if is_variant else list(resume.source_refs)
    source_ref_values.extend(
        ref for section in sections for entry in section.entries for ref in entry.source_refs
    )
    source_refs = tuple(dict.fromkeys(source_ref_values))
    return CanonicalProfessionalDocument(
        document_id=(resume.resume_variant_id if is_variant else resume.master_resume_id),
        document_kind="resume_variant" if is_variant else "master_resume",
        master_resume_id=resume.master_resume_id,
        resume_variant_id=resume.resume_variant_id if is_variant else "",
        title=resume.title,
        target_role=resume.target_role,
        summary="" if is_variant else resume.summary,
        sections=sections,
        source_profile_item_ids=tuple(resume.source_profile_item_ids),
        source_refs=source_refs,
    )


__all__ = [
    "CanonicalDocumentEntry",
    "CanonicalDocumentSection",
    "CanonicalProfessionalDocument",
    "ResumeDocument",
    "canonical_document",
]
