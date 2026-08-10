"""Deterministic taxonomy normalization with reviewable semantic fallbacks."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from difflib import SequenceMatcher

from modules.core.text_utils import normalize_text
from modules.taxonomy.models import (
    MappingMethod,
    NormalizedOccupation,
    NormalizedSkill,
    TaxonomyMapping,
)


class TaxonomyNormalizer:
    """Resolve exact/alias matches locally; fuzzy matches remain candidates."""

    def __init__(
        self,
        *,
        occupations: Iterable[NormalizedOccupation] = (),
        skills: Iterable[NormalizedSkill] = (),
    ) -> None:
        self.occupations = list(occupations)
        self.skills = list(skills)

    def map_occupation(self, value: str) -> TaxonomyMapping | None:
        return _map(value, self.occupations, kind="occupation")

    def map_skill(self, value: str) -> TaxonomyMapping | None:
        return _map(value, self.skills, kind="skill")


def _map(value: str, entries: Sequence[object], *, kind: str) -> TaxonomyMapping | None:
    source = value.strip()
    normalized_source = normalize_text(source)
    if not normalized_source:
        return None
    candidates: list[tuple[float, object, MappingMethod]] = []
    for entry in entries:
        label = _label(entry, kind)
        normalized_label = normalize_text(label)
        aliases = [normalize_text(alias) for alias in getattr(entry, "aliases", [])]
        if source == label:
            return _mapping(source, entry, label, kind, MappingMethod.EXACT, 1.0)
        if normalized_source == normalized_label:
            return _mapping(source, entry, label, kind, MappingMethod.NORMALIZED, 0.98)
        if normalized_source in aliases:
            return _mapping(source, entry, label, kind, MappingMethod.ALIAS, 0.95)
        similarity = max(
            [SequenceMatcher(None, normalized_source, normalized_label).ratio()]
            + [SequenceMatcher(None, normalized_source, alias).ratio() for alias in aliases]
        )
        candidates.append((similarity, entry, MappingMethod.SEMANTIC_CANDIDATE))
    if not candidates:
        return None
    similarity, entry, method = max(candidates, key=lambda candidate: candidate[0])
    if similarity < 0.72:
        return None
    return _mapping(source, entry, _label(entry, kind), kind, method, similarity)


def _mapping(
    source: str,
    entry: object,
    label: str,
    kind: str,
    method: MappingMethod,
    confidence: float,
) -> TaxonomyMapping:
    references = list(getattr(entry, "taxonomy_refs", []))
    return TaxonomyMapping(
        source_text=source,
        target_id=str(getattr(entry, "occupation_id" if kind == "occupation" else "skill_id")),
        target_label=label,
        taxonomy_ref=references[0] if references else "",
        match_method=method,
        confidence=round(confidence, 3),
        review_status="candidate",
    )


def _label(entry: object, kind: str) -> str:
    return str(getattr(entry, "canonical_title" if kind == "occupation" else "canonical_label"))


__all__ = ["TaxonomyNormalizer"]
