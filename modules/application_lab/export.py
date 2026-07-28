"""Honest, privacy-conscious Resume Studio exports."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal

from modules.application_lab.models import MasterResume, ResumeExport, ResumeSection, ResumeVariant
from modules.schemas.json_resume import CareerEvidence, JSONResume

ResumeDocument = MasterResume | ResumeVariant
ExportFormat = Literal["json_resume", "pdf", "docx"]


def prepare_resume_export(
    resume: ResumeDocument,
    *,
    export_format: ExportFormat,
    template_id: str = "classic",
) -> tuple[ResumeExport, dict[str, Any] | None]:
    """Build JSON Resume or report an honest pending state for future renderers."""
    master_resume_id = (
        resume.master_resume_id if isinstance(resume, MasterResume) else resume.master_resume_id
    )
    variant_id = resume.resume_variant_id if isinstance(resume, ResumeVariant) else ""
    stem = _safe_stem(resume.title or "curriculo")
    if export_format != "json_resume":
        pending = ResumeExport(
            master_resume_id=master_resume_id,
            resume_variant_id=variant_id,
            template_id=template_id,
            format=export_format,
            status="pending",
            file_name=f"{stem}.{export_format}",
            warnings=[
                f"Exportação {export_format.upper()} ainda não possui renderer maduro; "
                "use o preview ou JSON Resume nesta versão."
            ],
        )
        return pending, None

    document = _json_resume(resume)
    payload = document.model_dump(mode="json", exclude_none=True)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    ready = ResumeExport(
        master_resume_id=master_resume_id,
        resume_variant_id=variant_id,
        template_id=template_id,
        format="json_resume",
        status="ready",
        file_name=f"{stem}.resume.json",
        content_hash=hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
    )
    return ready, payload


def resume_plain_text(resume: ResumeDocument) -> str:
    """Render enabled content for snapshots and the local preview."""
    lines = [resume.title, resume.target_role]
    summary = resume.summary if isinstance(resume, MasterResume) else ""
    if summary:
        lines.append(summary)
    for section in sorted(resume.sections, key=lambda item: item.position):
        if not section.enabled:
            continue
        lines.extend([section.title, section.content])
        for entry in sorted(section.entries, key=lambda item: item.position):
            if entry.enabled:
                lines.extend([entry.title, entry.subtitle, entry.content])
    return "\n".join(item.strip() for item in lines if item.strip())


def _json_resume(resume: ResumeDocument) -> JSONResume:
    summary = resume.summary if isinstance(resume, MasterResume) else ""
    basics = {
        key: value
        for key, value in {"label": resume.target_role, "summary": summary}.items()
        if value
    }
    buckets: dict[str, list[dict[str, Any]]] = {
        "work": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certificates": [],
        "languages": [],
    }
    evidence: list[CareerEvidence] = []
    for section in resume.sections:
        if not section.enabled:
            continue
        bucket = _section_bucket(section)
        for entry in section.entries:
            if not entry.enabled or not entry.confirmed_by_user:
                continue
            item = _entry_payload(
                entry.title, entry.subtitle, entry.content, entry.start_date, entry.end_date
            )
            if bucket:
                buckets[bucket].append(item)
            for source_ref in entry.source_refs[:5]:
                evidence.append(
                    CareerEvidence(
                        fact=entry.title or entry.content[:120],
                        source="sotuhire",
                        source_ref=source_ref,
                        profile_item_id=(
                            entry.source_profile_item_ids[0]
                            if entry.source_profile_item_ids
                            else None
                        ),
                        evidence=entry.content or entry.title,
                        confidence=1.0,
                        can_use_in_resume=True,
                    )
                )
    return JSONResume(basics=basics, evidence=evidence, **buckets)


def _section_bucket(section: ResumeSection) -> str:
    normalized = re.sub(r"[^a-z_]", "", section.section_type.casefold())
    return {
        "experience": "work",
        "work_experience": "work",
        "education": "education",
        "skills": "skills",
        "projects": "projects",
        "portfolio": "projects",
        "certifications": "certificates",
        "professional_registry": "certificates",
        "professional_registrations": "certificates",
        "languages": "languages",
    }.get(normalized, "")


def _entry_payload(
    title: str, subtitle: str, content: str, start_date: str, end_date: str
) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "name": title,
            "position": title,
            "institution": subtitle,
            "summary": content,
            "startDate": start_date,
            "endDate": end_date,
            "keywords": [title] if title else [],
        }.items()
        if value
    }


def _safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-.")
    return cleaned[:80] or "curriculo"


__all__ = ["ExportFormat", "prepare_resume_export", "resume_plain_text"]
