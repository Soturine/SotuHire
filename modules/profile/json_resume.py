"""Safe interoperability between the Universal Profile and JSON Resume."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from modules.profile.models import ProfileItem, UniversalCareerProfile
from modules.schemas.json_resume import CareerEvidence, JSONResume

_WORK_TYPES = {
    "experience",
    "freelance_work",
    "volunteer_work",
    "internship",
    "residency",
    "clinical_practice",
    "teaching_practice",
    "laboratory_practice",
    "field_work",
}
_EDUCATION_TYPES = {"education", "technical_education", "postgraduate_education"}
_PROJECT_TYPES = {"project", "research", "research_project", "portfolio"}
_CERTIFICATE_TYPES = {"certification", "professional_registry", "standard_or_norm"}


def profile_to_json_resume(
    profile: UniversalCareerProfile,
    *,
    confirmed_only: bool = True,
) -> JSONResume:
    """Export non-sensitive profile facts, preserving SotuHire evidence metadata."""
    items = [
        item
        for item in [*profile.items, *profile.constraints]
        if not item.sensitive and (item.confirmed_by_user or not confirmed_only)
    ]
    basics = {
        key: value
        for key, value in {
            "name": profile.display_name,
            "label": profile.headline,
            "summary": profile.summary,
            "location": {"city": profile.preferred_locations[0]}
            if profile.preferred_locations
            else None,
        }.items()
        if value
    }
    return JSONResume(
        basics=basics,
        work=[_work_entry(item) for item in items if item.type in _WORK_TYPES],
        education=[_education_entry(item) for item in items if item.type in _EDUCATION_TYPES],
        skills=_skill_entries(items),
        projects=[_project_entry(item) for item in items if item.type in _PROJECT_TYPES],
        certificates=[
            _certificate_entry(item) for item in items if item.type in _CERTIFICATE_TYPES
        ],
        languages=[_language_entry(item) for item in items if item.type == "language_course"],
        evidence=[_evidence(item) for item in items if item.evidence],
    )


def json_resume_to_profile(
    resume: JSONResume | dict[str, object],
    *,
    profile_id: str = "default",
) -> UniversalCareerProfile:
    """Import JSON Resume as unconfirmed review candidates without writing to disk."""
    parsed = resume if isinstance(resume, JSONResume) else JSONResume.model_validate(resume)
    basics = parsed.basics
    locations = basics.get("location", {}) if isinstance(basics, dict) else {}
    city = locations.get("city") if isinstance(locations, dict) else None
    items: list[ProfileItem] = []
    items.extend(_items_from_entries("experience", parsed.work, "position", "name"))
    items.extend(_items_from_entries("education", parsed.education, "studyType", "institution"))
    items.extend(_items_from_entries("project", parsed.projects, "name"))
    items.extend(_items_from_entries("certification", parsed.certificates, "name", "issuer"))
    items.extend(_items_from_entries("language_course", parsed.languages, "language"))
    for entry in parsed.skills:
        if not isinstance(entry, dict):
            continue
        keywords = entry.get("keywords")
        values: list[object] = keywords if isinstance(keywords, list) else []
        names = [entry.get("name"), *values]
        for name in _unique(str(value) for value in names if value):
            items.append(_candidate("technical_skill", name, entry))
    return UniversalCareerProfile(
        profile_id=profile_id,
        display_name=_optional_string(basics.get("name")),
        headline=_optional_string(basics.get("label")),
        summary=_optional_string(basics.get("summary")),
        preferred_locations=[str(city)] if city else [],
        items=_dedupe(items),
    )


def _work_entry(item: ProfileItem) -> dict[str, object]:
    return _compact(
        {
            "name": item.organization,
            "position": item.title,
            "summary": item.description,
            "startDate": item.start_date,
            "endDate": item.end_date,
        }
    )


def _education_entry(item: ProfileItem) -> dict[str, object]:
    return _compact(
        {
            "institution": item.institution or item.organization,
            "studyType": item.title,
            "area": item.area,
            "startDate": item.start_date,
            "endDate": item.end_date,
        }
    )


def _project_entry(item: ProfileItem) -> dict[str, object]:
    return _compact(
        {
            "name": item.title,
            "description": item.description,
            "keywords": _unique([*item.skills, *item.tags]),
            "url": item.source_ref if str(item.source_ref or "").startswith("http") else None,
        }
    )


def _certificate_entry(item: ProfileItem) -> dict[str, object]:
    return _compact(
        {
            "name": item.title,
            "issuer": item.institution or item.organization,
            "date": item.end_date or item.start_date,
        }
    )


def _language_entry(item: ProfileItem) -> dict[str, object]:
    return _compact({"language": item.title, "fluency": item.status})


def _skill_entries(items: list[ProfileItem]) -> list[dict[str, object]]:
    names: list[str] = []
    for item in items:
        if item.type in {"technical_skill", "soft_skill"}:
            names.append(item.title)
        names.extend(item.skills)
    return [{"name": name, "keywords": [name]} for name in _unique(names)]


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
    entries: list[dict],
    *title_keys: str,
) -> list[ProfileItem]:
    result: list[ProfileItem] = []
    for entry in entries:
        title = next(
            (_optional_string(entry.get(key)) for key in title_keys if entry.get(key)), None
        )
        if title:
            result.append(_candidate(item_type, title, entry))
    return result


def _candidate(item_type: str, title: str, entry: dict[str, object]) -> ProfileItem:
    encoded = json.dumps(entry, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(f"{item_type}:{encoded}".encode()).hexdigest()[:24]
    return ProfileItem(
        type=item_type,
        title=title[:240],
        description=_optional_string(entry.get("summary") or entry.get("description")),
        institution=_optional_string(entry.get("institution")),
        organization=_optional_string(entry.get("name") or entry.get("issuer")),
        start_date=_optional_string(entry.get("startDate")),
        end_date=_optional_string(entry.get("endDate") or entry.get("date")),
        evidence=encoded[:5000],
        source="json_resume",
        source_ref=f"json-resume:{digest}",
        confidence="medium",
        confirmed_by_user=False,
    )


def _compact(value: dict[str, object]) -> dict[str, object]:
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
        key = (item.type, item.title.casefold())
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
