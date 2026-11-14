"""Project the Universal Profile into the Master Resume without retyping and without write-back.

Authority: the Universal Profile owns professional facts and their confirmation; the Master Resume is
an editable document derived from it; job variants derive from the Master Resume. Data only flows
downstream here, and only facts the user confirmed (and did not mark sensitive) are projected. An
entry keeps the profile item id in ``source_profile_item_ids`` so a later projection can tell
which confirmed facts the resume does not contain yet. Nothing in this module writes the profile.
"""

from __future__ import annotations

from datetime import UTC, datetime

from modules.application_lab.models import MasterResume, ResumeEntry, ResumeSection
from modules.profile.json_resume import section_for_item
from modules.profile.models import ProfileItem, UniversalCareerProfile

# JSON Resume section -> (resume section_type, title). Order is the resume order. References are
# not projected: they name third parties.
SECTION_LAYOUT: tuple[tuple[str, str, str], ...] = (
    ("work", "experience", "Experiência"),
    ("education", "education", "Formação"),
    ("projects", "projects", "Projetos"),
    ("certificates", "certifications", "Certificações e registros"),
    ("skills", "skills", "Competências"),
    ("languages", "languages", "Idiomas"),
    ("publications", "publications", "Publicações"),
    ("awards", "awards", "Prêmios"),
    ("volunteer", "volunteer", "Voluntariado"),
    ("interests", "interests", "Interesses"),
)
_LAYOUT = {source: (section_type, title) for source, section_type, title in SECTION_LAYOUT}


def projectable_items(profile: UniversalCareerProfile) -> list[ProfileItem]:
    """Confirmed, non-sensitive profile items that have a resume section."""
    return [
        item
        for item in profile.items
        if item.confirmed_by_user and not item.sensitive and section_for_item(item) in _LAYOUT
    ]


def master_resume_from_profile(profile: UniversalCareerProfile) -> MasterResume:
    """Build a new Master Resume from the confirmed facts of the profile."""
    items = projectable_items(profile)
    sections = _sections(items)
    skipped = [item for item in profile.items if not item.confirmed_by_user and not item.sensitive]
    warnings = (
        [
            f"{len(skipped)} item(ns) do Perfil ainda não confirmado(s) ficaram de fora; "
            "confirme no Perfil para trazê-los."
        ]
        if skipped
        else []
    )
    return MasterResume(
        profile_id=profile.profile_id,
        title="Currículo Mestre",
        target_role=(profile.target_roles[0] if profile.target_roles else profile.headline or ""),
        summary=profile.summary or "",
        source_type="profile",
        source_refs=[f"profile:{profile.profile_id}"],
        source_profile_item_ids=[item.item_id for item in items],
        sections=sections,
        validation_warnings=warnings,
    )


def profile_updates(profile: UniversalCareerProfile, master: MasterResume) -> list[ProfileItem]:
    """Confirmed profile facts that no entry of the Master Resume was built from yet."""
    present = {
        item_id
        for section in master.sections
        for entry in section.entries
        for item_id in entry.source_profile_item_ids
    }
    return [item for item in projectable_items(profile) if item.item_id not in present]


def apply_profile_updates(
    master: MasterResume, profile: UniversalCareerProfile, item_ids: list[str]
) -> MasterResume:
    """Append the chosen confirmed profile facts to the Master Resume; existing entries are kept."""
    chosen = set(item_ids)
    pending = {item.item_id: item for item in profile_updates(profile, master)}
    unknown = chosen - set(pending)
    if unknown:
        raise ValueError(
            "Itens não disponíveis para o Currículo Mestre (não confirmados, sensíveis ou já "
            "presentes): " + ", ".join(sorted(unknown))
        )
    sections = [section.model_copy(deep=True) for section in master.sections]
    by_type = {section.section_type: section for section in sections}
    now = datetime.now(UTC)
    for item in (pending[item_id] for item_id in item_ids):
        section_type, title = _LAYOUT[section_for_item(item)]
        section = by_type.get(section_type)
        if section is None:
            section = ResumeSection(section_type=section_type, title=title, position=len(sections))
            sections.append(section)
            by_type[section_type] = section
        section.entries.append(_entry(item, position=len(section.entries)))
        section.updated_at = now
    return master.model_copy(
        update={
            "sections": sections,
            "source_profile_item_ids": list(
                dict.fromkeys([*master.source_profile_item_ids, *item_ids])
            ),
            "updated_at": now,
        }
    )


def _sections(items: list[ProfileItem]) -> list[ResumeSection]:
    grouped: dict[str, list[ProfileItem]] = {}
    for item in items:
        grouped.setdefault(section_for_item(item), []).append(item)
    sections: list[ResumeSection] = []
    for source, section_type, title in SECTION_LAYOUT:
        members = grouped.get(source, [])
        if not members:
            continue
        sections.append(
            ResumeSection(
                section_type=section_type,
                title=title,
                position=len(sections),
                entries=[_entry(item, position=index) for index, item in enumerate(members)],
            )
        )
    return sections


def _entry(item: ProfileItem, *, position: int) -> ResumeEntry:
    return ResumeEntry(
        entry_type=item.type,
        title=item.title,
        subtitle=item.organization or item.institution or "",
        content=item.description or item.evidence or "",
        start_date=item.start_date or "",
        end_date=item.end_date or "",
        position=position,
        source_profile_item_ids=[item.item_id],
        source_refs=[item.source_ref] if item.source_ref else [],
        confirmed_by_user=True,
    )


__all__ = [
    "SECTION_LAYOUT",
    "apply_profile_updates",
    "master_resume_from_profile",
    "profile_updates",
    "projectable_items",
]
