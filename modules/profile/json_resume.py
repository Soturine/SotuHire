"""Semantic JSON Resume interoperability for the Universal Career Profile."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from modules.profile.models import (
    ProfileInteroperability,
    ProfileItem,
    UniversalCareerProfile,
)
from modules.schemas.json_resume import CareerEvidence, JSONResume

_WORK_TYPES = {
    "experience",
    "freelance_work",
    "internship",
    "residency",
    "clinical_practice",
    "teaching_practice",
    "laboratory_practice",
    "field_work",
}
_VOLUNTEER_TYPES = {"volunteer", "volunteer_work"}
_EDUCATION_TYPES = {"education", "technical_education", "postgraduate_education"}
_PROJECT_TYPES = {"project", "research", "research_project", "portfolio"}
_CERTIFICATE_TYPES = {"certification", "certificate", "standard_or_norm"}
_PROFESSIONAL_REGISTRATION_TYPES = {
    "professional_registry",
    "professional_registration",
    "professional_license",
}
_SECTION_SPECS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("work", "experience", ("position", "name")),
    ("volunteer", "volunteer_work", ("position", "organization")),
    ("education", "education", ("studyType", "area", "institution")),
    ("awards", "award", ("title", "awarder")),
    ("certificates", "certification", ("name", "issuer")),
    ("publications", "publication", ("name", "publisher")),
    ("skills", "technical_skill", ("name",)),
    ("languages", "language", ("language",)),
    ("interests", "interest", ("name",)),
    ("references", "reference", ("name", "reference")),
    ("projects", "project", ("name",)),
)


def profile_to_json_resume(
    profile: UniversalCareerProfile,
    *,
    confirmed_only: bool = True,
) -> JSONResume:
    """Export profile facts through section-specific JSON Resume mappers."""
    items = [
        item
        for item in [*profile.items, *profile.constraints]
        if not item.sensitive and (item.confirmed_by_user or not confirmed_only)
    ]
    basics = dict(profile.interoperability.json_resume_basics)
    location = basics.get("location")
    preserved_location = dict(location) if isinstance(location, dict) else {}
    if profile.preferred_locations:
        preserved_location["city"] = profile.preferred_locations[0]
    basics.update(
        {
            key: value
            for key, value in {
                "name": profile.display_name,
                "label": profile.headline,
                "summary": profile.summary,
                "location": preserved_location or None,
            }.items()
            if value
        }
    )
    sections: dict[str, list[dict[str, Any]]] = {name: [] for name, _, _ in _SECTION_SPECS}
    professional_registrations: list[dict[str, Any]] = []
    for item in items:
        if item.type in _PROFESSIONAL_REGISTRATION_TYPES:
            professional_registrations.append(_entry_from_item(item, "professional_registrations"))
            continue
        section = _section_for_item(item)
        if section:
            sections[section].append(_entry_from_item(item, section))

    extension = dict(profile.interoperability.json_resume_extension)
    extension["professionalRegistrations"] = professional_registrations
    payload: dict[str, Any] = {
        **profile.interoperability.json_resume_extra,
        "$schema": profile.interoperability.json_resume_schema_url,
        "basics": basics,
        **sections,
        "meta": dict(profile.interoperability.json_resume_meta),
        "x-sotuhire": extension,
        "evidence": [
            *(profile.interoperability.json_resume_evidence if not confirmed_only else []),
            *[_evidence(item).model_dump(mode="json") for item in items if item.evidence],
        ],
    }
    return JSONResume.model_validate(payload)


def json_resume_to_profile(
    resume: JSONResume | dict[str, object],
    *,
    profile_id: str = "default",
) -> UniversalCareerProfile:
    """Import every supported JSON Resume section as reviewable candidates."""
    parsed = resume if isinstance(resume, JSONResume) else JSONResume.model_validate(resume)
    basics = parsed.basics
    locations = basics.get("location", {}) if isinstance(basics, dict) else {}
    city = locations.get("city") if isinstance(locations, dict) else None
    items: list[ProfileItem] = []
    for section, item_type, title_keys in _SECTION_SPECS:
        entries = getattr(parsed, section)
        items.extend(_items_from_entries(item_type, entries, *title_keys))
    items.extend(
        _items_from_entries(
            "professional_registration",
            parsed.sotuhire.professional_registrations,
            "name",
            "registration",
            "authority",
        )
    )
    extras = dict(parsed.__pydantic_extra__ or {})
    extension = parsed.sotuhire.model_dump(mode="json", by_alias=True)
    return UniversalCareerProfile(
        profile_id=profile_id,
        display_name=_optional_string(basics.get("name")),
        headline=_optional_string(basics.get("label")),
        summary=_optional_string(basics.get("summary")),
        preferred_locations=[str(city)] if city else [],
        items=_dedupe(items),
        interoperability=ProfileInteroperability(
            json_resume_schema_url=parsed.schema_url,
            json_resume_basics=dict(parsed.basics),
            json_resume_meta=dict(parsed.meta),
            json_resume_extension=extension,
            json_resume_extra=extras,
            json_resume_evidence=[item.model_dump(mode="json") for item in parsed.evidence],
        ),
    )


def _section_for_item(item: ProfileItem) -> str:
    if item.type in _WORK_TYPES:
        return "work"
    if item.type in _VOLUNTEER_TYPES:
        return "volunteer"
    if item.type in _EDUCATION_TYPES:
        return "education"
    if item.type in {"award", "awards"}:
        return "awards"
    if item.type in _CERTIFICATE_TYPES:
        return "certificates"
    if item.type in {"publication", "publications"}:
        return "publications"
    if item.type in {"technical_skill", "soft_skill", "skill"}:
        return "skills"
    if item.type in {"language", "language_course"}:
        return "languages"
    if item.type in {"interest", "interests"}:
        return "interests"
    if item.type in {"reference", "references"}:
        return "references"
    if item.type in _PROJECT_TYPES:
        return "projects"
    return ""


def _entry_from_item(item: ProfileItem, section: str) -> dict[str, Any]:
    raw = _raw_entry(item)
    if raw:
        return _overlay_entry(raw, item, section)
    if section in {"work", "volunteer"}:
        return _compact(
            {
                "name" if section == "work" else "organization": item.organization,
                "position": item.title,
                "summary": item.description,
                "startDate": item.start_date,
                "endDate": item.end_date,
            }
        )
    if section == "education":
        return _compact(
            {
                "institution": item.institution or item.organization,
                "studyType": item.title,
                "area": item.area,
                "startDate": item.start_date,
                "endDate": item.end_date,
            }
        )
    if section == "awards":
        return _compact(
            {
                "title": item.title,
                "awarder": item.organization or item.institution,
                "date": item.end_date or item.start_date,
                "summary": item.description,
            }
        )
    if section == "certificates":
        return _compact(
            {
                "name": item.title,
                "issuer": item.institution or item.organization,
                "date": item.end_date or item.start_date,
                "url": item.source_ref if str(item.source_ref or "").startswith("http") else None,
            }
        )
    if section == "publications":
        return _compact(
            {
                "name": item.title,
                "publisher": item.organization or item.institution,
                "releaseDate": item.end_date or item.start_date,
                "summary": item.description,
                "url": item.source_ref if str(item.source_ref or "").startswith("http") else None,
            }
        )
    if section == "skills":
        return _compact({"name": item.title, "level": item.status, "keywords": item.skills})
    if section == "languages":
        return _compact({"language": item.title, "fluency": item.status})
    if section == "interests":
        return _compact({"name": item.title, "keywords": [*item.skills, *item.tags]})
    if section == "references":
        return _compact({"name": item.title, "reference": item.description})
    if section == "professional_registrations":
        return _compact(
            {
                "name": item.title,
                "authority": item.organization or item.institution,
                "status": item.status,
                "date": item.end_date or item.start_date,
                "summary": item.description,
                "sourceRefs": [item.source_ref] if item.source_ref else [],
            }
        )
    return _compact(
        {
            "name": item.title,
            "description": item.description,
            "keywords": _unique([*item.skills, *item.tags]),
            "startDate": item.start_date,
            "endDate": item.end_date,
            "url": item.source_ref if str(item.source_ref or "").startswith("http") else None,
        }
    )


def _overlay_entry(raw: dict[str, Any], item: ProfileItem, section: str) -> dict[str, Any]:
    result = dict(raw)
    title_key = {
        "work": "position",
        "volunteer": "position",
        "education": "studyType",
        "awards": "title",
        "certificates": "name",
        "publications": "name",
        "skills": "name",
        "languages": "language",
        "interests": "name",
        "references": "name",
        "projects": "name",
        "professional_registrations": "name",
    }.get(section)
    if title_key:
        result[title_key] = item.title
    return result


def _raw_entry(item: ProfileItem) -> dict[str, Any]:
    if item.source != "json_resume":
        return {}
    if item.structured_data:
        return dict(item.structured_data)
    if not item.evidence:
        return {}
    try:
        value = json.loads(item.evidence)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _evidence(item: ProfileItem) -> CareerEvidence:
    confidence = {"low": 0.4, "medium": 0.7, "high": 0.95}[item.confidence]
    return CareerEvidence(
        fact=item.title,
        source=item.source,
        source_ref=item.source_ref,
        profile_item_id=item.item_id,
        evidence=item.evidence or item.description or item.title,
        confidence=confidence,
        can_use_in_resume=item.confirmed_by_user and not item.sensitive,
        last_verified_at=item.updated_at.isoformat(),
    )


def _items_from_entries(
    item_type: str,
    entries: list[dict[str, Any]],
    *title_keys: str,
) -> list[ProfileItem]:
    result: list[ProfileItem] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        title = next(
            (_optional_string(entry.get(key)) for key in title_keys if entry.get(key)), None
        )
        if title:
            result.append(_candidate(item_type, title, entry))
    return result


def _candidate(item_type: str, title: str, entry: dict[str, Any]) -> ProfileItem:
    encoded = json.dumps(entry, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(f"{item_type}:{encoded}".encode()).hexdigest()[:24]
    keywords = entry.get("keywords")
    skills = [str(value) for value in keywords] if isinstance(keywords, list) else []
    return ProfileItem(
        type=item_type,
        title=title[:240],
        description=_optional_string(
            entry.get("summary") or entry.get("description") or entry.get("reference")
        ),
        area=_optional_string(entry.get("area")),
        institution=_optional_string(entry.get("institution")),
        organization=_optional_string(
            entry.get("organization")
            or entry.get("name")
            or entry.get("issuer")
            or entry.get("publisher")
            or entry.get("awarder")
            or entry.get("authority")
        ),
        status=_optional_string(entry.get("status") or entry.get("level") or entry.get("fluency")),
        start_date=_optional_string(entry.get("startDate")),
        end_date=_optional_string(
            entry.get("endDate") or entry.get("date") or entry.get("releaseDate")
        ),
        skills=skills,
        evidence=encoded[:5000],
        structured_data=dict(entry),
        source="json_resume",
        source_ref=f"json-resume:{digest}",
        confidence="medium",
        confirmed_by_user=False,
    )


def _compact(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, "", [])}


def _optional_string(value: object) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _dedupe(items: list[ProfileItem]) -> list[ProfileItem]:
    result: list[ProfileItem] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        identity = item.source_ref or item.title.casefold()
        key = (item.type, identity)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
