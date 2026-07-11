"""Universal career profile application service."""

from __future__ import annotations

from collections.abc import Iterable

from modules.core.deduplication import duplicate_groups
from modules.core.entity_identity import profile_item_identity
from modules.core.text_utils import normalize_text
from modules.profile.extraction import extract_profile_items_local
from modules.profile.models import (
    ProfileDeduplicationSuggestion,
    ProfileImportDraft,
    ProfileItem,
    ProfileSourceSummary,
    UniversalCareerProfile,
    utc_now,
)
from modules.profile.store import UniversalCareerProfileStore


class UniversalCareerProfileService:
    """Manage the active local universal career profile."""

    def __init__(self, store: UniversalCareerProfileStore | None = None) -> None:
        self.store = store or UniversalCareerProfileStore()

    def get_profile(self) -> UniversalCareerProfile:
        """Return the active profile, creating a default when needed."""
        return self.store.load_active()

    def update_profile(self, updates: dict[str, object]) -> UniversalCareerProfile:
        """Update profile-level fields."""
        profile = self.get_profile()
        allowed = {
            "display_name",
            "headline",
            "summary",
            "primary_domains",
            "secondary_domains",
            "career_moments",
            "target_roles",
            "target_seniority",
            "preferred_locations",
            "preferred_work_models",
            "preferred_contract_types",
        }
        data = profile.model_dump()
        for key, value in updates.items():
            if key in allowed:
                data[key] = value
        data["updated_at"] = utc_now()
        updated = UniversalCareerProfile.model_validate(data)
        return self._save_with_summaries(updated)

    def add_item(self, item: ProfileItem, *, confirmed_by_user: bool = True) -> ProfileItem:
        """Add one reviewed item to the profile."""
        profile = self.get_profile()
        now = utc_now()
        item = item.model_copy(
            update={
                "confirmed_by_user": confirmed_by_user,
                "confidence": "high" if confirmed_by_user else item.confidence,
                "created_at": item.created_at or now,
                "updated_at": now,
            }
        )
        if item.type == "constraint":
            profile.constraints.append(item)
        else:
            profile.items.append(item)
        profile = profile.model_copy(update={"updated_at": now})
        self._save_with_summaries(profile)
        return item

    def patch_item(self, item_id: str, updates: dict[str, object]) -> ProfileItem:
        """Patch one item and mark manual edits as confirmed."""
        profile = self.get_profile()
        all_items = [*profile.items, *profile.constraints]
        for item in all_items:
            if item.item_id == item_id:
                data = item.model_dump()
                for key, value in updates.items():
                    if value is not None and key in data:
                        data[key] = value
                data["confirmed_by_user"] = True
                data["updated_at"] = utc_now()
                updated = ProfileItem.model_validate(data)
                profile.items = [
                    updated if current.item_id == item_id else current for current in profile.items
                ]
                profile.constraints = [
                    updated if current.item_id == item_id else current
                    for current in profile.constraints
                ]
                self._save_with_summaries(profile.model_copy(update={"updated_at": utc_now()}))
                return updated
        raise KeyError("Item de perfil nao encontrado.")

    def delete_item(self, item_id: str) -> UniversalCareerProfile:
        """Remove one profile item from the local profile."""
        profile = self.get_profile()
        before = len(profile.items) + len(profile.constraints)
        profile.items = [item for item in profile.items if item.item_id != item_id]
        profile.constraints = [item for item in profile.constraints if item.item_id != item_id]
        after = len(profile.items) + len(profile.constraints)
        if before == after:
            raise KeyError("Item de perfil nao encontrado.")
        return self._save_with_summaries(profile.model_copy(update={"updated_at": utc_now()}))

    def import_text_local(
        self,
        text: str,
        *,
        source_type: str,
        warnings: Iterable[str] = (),
    ) -> ProfileImportDraft:
        """Return local draft items without saving them."""
        return extract_profile_items_local(text, source_type=source_type, warnings=warnings)

    def deduplicate(self) -> list[ProfileDeduplicationSuggestion]:
        """Return safe duplicate suggestions without deleting evidence."""
        profile = self.get_profile()
        suggestions: list[ProfileDeduplicationSuggestion] = []
        for items in duplicate_groups(
            [*profile.items, *profile.constraints], _profile_item_identity
        ):
            suggestions.append(
                ProfileDeduplicationSuggestion(
                    item_ids=[item.item_id for item in items],
                    reason=(
                        "Mesma referencia de origem ou conteudo normalizado; "
                        "revise antes de mesclar."
                    ),
                    confidence="high" if len({item.source for item in items}) > 1 else "medium",
                    proposed_title=items[0].title,
                    proposed_description=items[0].description,
                    sources=_unique(item.source for item in items),
                )
            )
        return suggestions

    def _save_with_summaries(self, profile: UniversalCareerProfile) -> UniversalCareerProfile:
        profile = profile.model_copy(update={"source_summaries": _source_summaries(profile)})
        return self.store.save_active(profile)


def _source_summaries(profile: UniversalCareerProfile) -> list[ProfileSourceSummary]:
    grouped: dict[str, list[ProfileItem]] = {}
    for item in [*profile.items, *profile.constraints]:
        grouped.setdefault(item.source, []).append(item)
    summaries = []
    for source, items in grouped.items():
        summaries.append(
            ProfileSourceSummary(
                source=source,
                source_type=source,
                item_count=len(items),
                last_imported_at=max(item.updated_at for item in items),
            )
        )
    return sorted(summaries, key=lambda item: item.source)


def _unique(values: Iterable[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and normalize_text(cleaned) not in {
            normalize_text(existing) for existing in unique
        }:
            unique.append(cleaned)
    return unique


def _profile_item_identity(item: ProfileItem) -> str:
    return profile_item_identity(
        item_type=item.type,
        title=item.title,
        source=item.source,
        source_ref=item.source_ref or "",
        evidence=item.evidence or item.description or "",
    )
