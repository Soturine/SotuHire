"""Service layer for Lattes imports and academic profile confirmation."""

from __future__ import annotations

from collections.abc import Iterable

from modules.academic.lattes_models import (
    LattesConfirmResult,
    LattesImportInput,
    LattesImportResult,
)
from modules.academic.lattes_parser import parse_lattes_text
from modules.ai.prompt_registry import PromptRegistry
from modules.ai.providers import AIProvider
from modules.core.text_utils import normalize_text
from modules.profile.models import ProfileItem, utc_now
from modules.profile.service import UniversalCareerProfileService


class LattesService:
    """Extract and confirm academic evidence without auto-saving drafts."""

    def draft_local(
        self,
        payload: LattesImportInput,
        *,
        warnings: Iterable[str] = (),
    ) -> LattesImportResult:
        """Return local, review-only academic evidence drafts."""
        result = parse_lattes_text(payload)
        if warnings:
            result = result.model_copy(update={"warnings": [*warnings, *result.warnings]})
        return result

    def draft_with_ai(
        self,
        payload: LattesImportInput,
        *,
        provider: AIProvider,
        prompt_registry: PromptRegistry,
        provider_name: str,
        requested_provider: str,
        warnings: Iterable[str] = (),
    ) -> LattesImportResult:
        """Ask an optional provider for structured drafts, falling back locally on failure."""
        local = self.draft_local(payload, warnings=warnings)
        try:
            spec = prompt_registry.get("profile_lattes_extractor_v1")
            output = provider.generate_structured(
                spec,
                {
                    "text": payload.text,
                    "source_url": payload.source_url,
                    "lattes_id": payload.lattes_id,
                    "orcid": payload.orcid,
                    "language": payload.language,
                    "local_parser_draft": local.model_dump(mode="json"),
                },
            )
            draft = LattesImportResult.model_validate(output)
            normalized = [
                _candidate_for_lattes(item, payload) for item in draft.items if item.title.strip()
            ]
            return draft.model_copy(
                update={
                    "items": _dedupe_items(normalized),
                    "detected_sections": draft.detected_sections or local.detected_sections,
                    "assumptions": [*local.assumptions, *draft.assumptions],
                    "warnings": [
                        *warnings,
                        *draft.warnings,
                        "Itens sugeridos pela IA exigem revisão humana antes de entrar no Perfil.",
                    ],
                    "needs_user_review": True,
                    "provider_used": provider_name,
                    "requested_provider": requested_provider,
                    "analysis_mode": "ai",
                }
            )
        except Exception:
            return local.model_copy(
                update={
                    "warnings": [
                        *local.warnings,
                        "IA indisponível ou resposta inválida; usei parser local de Lattes.",
                    ],
                    "requested_provider": requested_provider,
                    "analysis_mode": "fallback",
                }
            )

    def confirm_items(
        self,
        items: Iterable[ProfileItem],
        *,
        profile_service: UniversalCareerProfileService | None = None,
    ) -> LattesConfirmResult:
        """Save explicitly selected items into the Universal Career Profile."""
        service = profile_service or UniversalCareerProfileService()
        profile = service.get_profile()
        existing_keys = {_profile_key(item) for item in [*profile.items, *profile.constraints]}
        saved: list[ProfileItem] = []
        skipped: list[ProfileItem] = []
        now = utc_now()
        for item in items:
            candidate = _candidate_for_lattes(
                item, LattesImportInput(text=item.evidence or item.title)
            )
            key = _profile_key(candidate)
            if key in existing_keys:
                skipped.append(candidate)
                continue
            confirmed = candidate.model_copy(
                update={
                    "confirmed_by_user": True,
                    "updated_at": now,
                    "confidence": "high"
                    if candidate.confidence == "high"
                    else candidate.confidence,
                }
            )
            saved_item = service.add_item(confirmed, confirmed_by_user=True)
            saved.append(saved_item)
            existing_keys.add(key)
        return LattesConfirmResult(
            saved=saved,
            skipped_duplicates=skipped,
            message=f"{len(saved)} item(ns) acadêmico(s) adicionados ao Perfil Profissional Universal.",
        )


def _candidate_for_lattes(item: ProfileItem, payload: LattesImportInput) -> ProfileItem:
    source_ref = item.source_ref or payload.lattes_id or payload.source_url or payload.orcid or None
    source = item.source if item.source and item.source != "manual" else "curriculum_lattes"
    return item.model_copy(
        update={
            "source": source,
            "source_ref": source_ref,
            "evidence": (item.evidence or item.description or item.title)[:5000],
            "confirmed_by_user": False,
            "sensitive": bool(item.sensitive),
        }
    )


def _profile_key(item: ProfileItem) -> str:
    return normalize_text(" ".join([item.type, item.title, item.source, item.source_ref or ""]))


def _dedupe_items(items: list[ProfileItem]) -> list[ProfileItem]:
    unique: list[ProfileItem] = []
    seen: set[str] = set()
    for item in items:
        key = _profile_key(item)
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
