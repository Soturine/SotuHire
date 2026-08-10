"""Canonical opportunity provenance, deduplication, and deterministic ranking."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from difflib import SequenceMatcher
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field

from modules.core.text_utils import normalize_text

SourceKind = Literal[
    "greenhouse",
    "lever",
    "schema_org",
    "rss",
    "atom",
    "manual",
    "extension",
    "radar",
]


def utc_now() -> datetime:
    return datetime.now(UTC)


class OpportunityProvenance(BaseModel):
    """Immutable observation metadata for one public source response."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    external_id: str = ""
    url: str
    retrieved_at: datetime = Field(default_factory=utc_now)
    source_version: str = ""
    content_hash: str
    collection_method: str = "public_api"


class OpportunityCandidate(BaseModel):
    """Common source-neutral candidate produced before persistence or ranking."""

    model_config = ConfigDict(extra="forbid")

    source: str
    source_kind: SourceKind
    source_url: str
    external_id: str = ""
    title: str = Field(min_length=1, max_length=300)
    organization: str = Field(default="", max_length=300)
    location: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=100_000)
    employment_type: str = Field(default="", max_length=160)
    posted_at: datetime | None = None
    valid_through: datetime | None = None
    salary: dict[str, Any] = Field(default_factory=dict)
    remote: bool | None = None
    structured_data: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)
    content_hash: str = ""
    collected_at: datetime = Field(default_factory=utc_now)
    provenance: list[OpportunityProvenance] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.content_hash:
            payload = {
                "title": self.title,
                "organization": self.organization,
                "location": self.location,
                "description": self.description,
                "employment_type": self.employment_type,
                "valid_through": self.valid_through.isoformat() if self.valid_through else "",
            }
            self.content_hash = hashlib.sha256(
                json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
        self.source_refs = list(dict.fromkeys([self.source_url, *self.source_refs]))
        if not self.provenance:
            self.provenance = [
                OpportunityProvenance(
                    provider=self.source,
                    external_id=self.external_id,
                    url=self.source_url,
                    retrieved_at=self.collected_at,
                    content_hash=self.content_hash,
                    collection_method=self.source_kind,
                )
            ]


class OpportunityMerge(BaseModel):
    """Reviewable result of combining source observations for one vacancy."""

    model_config = ConfigDict(extra="forbid")

    candidate: OpportunityCandidate
    duplicate_count: int = 0
    merge_reasons: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0, le=1)
    review_required: bool = False


class OpportunityRank(BaseModel):
    """Explainable local ranking with separate fit, confidence, and coverage."""

    model_config = ConfigDict(extra="forbid")

    candidate: OpportunityCandidate
    fit_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence_coverage: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    ai_enrichment: dict[str, Any] = Field(default_factory=dict)


class OpportunityPreferences(BaseModel):
    """Minimum confirmed context used by the deterministic local ranker."""

    model_config = ConfigDict(extra="forbid")

    target_titles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_preferred: bool | None = None
    seniority: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)


def deduplicate_opportunities(
    candidates: Iterable[OpportunityCandidate],
) -> list[OpportunityMerge]:
    """Merge only high-confidence identities and retain all source observations."""
    merged: list[OpportunityMerge] = []
    for candidate in candidates:
        match: tuple[int, str, float] | None = None
        for index, existing in enumerate(merged):
            reason, confidence = _duplicate_reason(existing.candidate, candidate)
            if reason and (match is None or confidence > match[2]):
                match = (index, reason, confidence)
        if match is None:
            merged.append(OpportunityMerge(candidate=candidate))
            continue
        index, reason, confidence = match
        current = merged[index]
        if confidence < 0.86:
            merged.append(
                OpportunityMerge(
                    candidate=candidate,
                    merge_reasons=[reason],
                    confidence=confidence,
                    review_required=True,
                )
            )
            continue
        current.candidate = _merge_candidate(current.candidate, candidate)
        current.duplicate_count += 1
        current.merge_reasons = list(dict.fromkeys([*current.merge_reasons, reason]))
        current.confidence = min(current.confidence, confidence)
    return merged


def rank_opportunities(
    candidates: Iterable[OpportunityCandidate],
    preferences: OpportunityPreferences,
    *,
    top_k: int = 20,
    ai_enricher: Callable[[OpportunityCandidate], dict[str, Any]] | None = None,
) -> list[OpportunityRank]:
    """Rank locally first and invoke optional AI only for the bounded top-K."""
    ranked = [_rank(candidate, preferences) for candidate in candidates]
    ranked.sort(key=lambda item: (-item.fit_score, -item.confidence, item.candidate.title))
    selected = ranked[: max(0, min(top_k, 100))]
    if ai_enricher:
        for item in selected:
            item.ai_enrichment = dict(ai_enricher(item.candidate))
    return selected


def canonical_opportunity_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    host = (parsed.hostname or "").casefold()
    port = parsed.port
    netloc = host if port in {None, 80, 443} else f"{host}:{port}"
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.casefold(), netloc, path, "", ""))


def _duplicate_reason(
    left: OpportunityCandidate,
    right: OpportunityCandidate,
) -> tuple[str, float]:
    if (
        left.external_id
        and right.external_id
        and normalize_text(left.source) == normalize_text(right.source)
        and left.external_id == right.external_id
    ):
        return "provider_external_id", 1.0
    if canonical_opportunity_url(left.source_url) == canonical_opportunity_url(right.source_url):
        return "canonical_url", 0.99
    same_org = bool(left.organization) and normalize_text(left.organization) == normalize_text(
        right.organization
    )
    same_title = normalize_text(left.title) == normalize_text(right.title)
    same_location = normalize_text(left.location) == normalize_text(right.location)
    if same_org and same_title and same_location:
        return "organization_title_location", 0.93
    if not same_org:
        return "", 0.0
    similarity = SequenceMatcher(
        None,
        normalize_text(f"{left.title} {left.location}"),
        normalize_text(f"{right.title} {right.location}"),
    ).ratio()
    if similarity >= 0.82:
        return "semantic_similarity_candidate", min(0.85, similarity)
    return "", 0.0


def _merge_candidate(
    current: OpportunityCandidate,
    incoming: OpportunityCandidate,
) -> OpportunityCandidate:
    preferred = incoming if incoming.collected_at >= current.collected_at else current
    return preferred.model_copy(
        update={
            "source_refs": list(dict.fromkeys([*current.source_refs, *incoming.source_refs])),
            "provenance": [*current.provenance, *incoming.provenance],
        }
    )


def _rank(
    candidate: OpportunityCandidate,
    preferences: OpportunityPreferences,
) -> OpportunityRank:
    text = normalize_text(
        " ".join(
            [
                candidate.title,
                candidate.organization,
                candidate.location,
                candidate.description,
                candidate.employment_type,
            ]
        )
    )
    reasons: list[str] = []
    gaps: list[str] = []
    components: list[tuple[float, float]] = []

    title_match = _best_overlap(candidate.title, preferences.target_titles)
    components.append((title_match, 0.32))
    if title_match >= 0.7:
        reasons.append("Cargo alinhado ao objetivo confirmado.")

    skills = [skill for skill in preferences.skills if normalize_text(skill) in text]
    skill_coverage = len(skills) / len(preferences.skills) if preferences.skills else 0.5
    components.append((skill_coverage, 0.30))
    if skills:
        reasons.append(f"Competencias encontradas: {', '.join(skills[:5])}.")
    gaps.extend(skill for skill in preferences.skills if skill not in skills)

    location_match = _best_overlap(candidate.location, preferences.locations)
    if candidate.remote and preferences.remote_preferred:
        location_match = max(location_match, 1.0)
    components.append((location_match, 0.16))

    seniority_match = max(
        (1.0 if normalize_text(value) in text else 0.0 for value in preferences.seniority),
        default=0.5,
    )
    components.append((seniority_match, 0.10))

    source_quality = {
        "greenhouse": 1.0,
        "lever": 1.0,
        "schema_org": 0.85,
        "rss": 0.75,
        "atom": 0.75,
        "manual": 0.6,
        "extension": 0.7,
        "radar": 0.65,
    }[candidate.source_kind]
    freshness = _freshness(candidate.posted_at or candidate.collected_at)
    components.extend([(source_quality, 0.07), (freshness, 0.05)])

    excluded = [term for term in preferences.excluded_terms if normalize_text(term) in text]
    penalty = min(0.5, len(excluded) * 0.25)
    if excluded:
        gaps.append(f"Termos excluidos: {', '.join(excluded)}")
    fit = max(0.0, sum(value * weight for value, weight in components) - penalty)
    evidence_dimensions = sum(
        bool(value)
        for value in (
            candidate.description,
            candidate.location,
            candidate.employment_type,
            candidate.posted_at,
            candidate.external_id,
        )
    )
    evidence_coverage = evidence_dimensions / 5
    confidence = min(1.0, 0.45 + evidence_coverage * 0.35 + source_quality * 0.2)
    return OpportunityRank(
        candidate=candidate,
        fit_score=round(fit * 100, 2),
        confidence=round(confidence, 3),
        evidence_coverage=round(evidence_coverage, 3),
        reasons=reasons,
        gaps=gaps[:10],
    )


def _best_overlap(value: str, targets: list[str]) -> float:
    if not targets:
        return 0.5
    normalized = normalize_text(value)
    return max(
        SequenceMatcher(None, normalized, normalize_text(target)).ratio() for target in targets
    )


def _freshness(value: datetime) -> float:
    current = value if value.tzinfo else value.replace(tzinfo=UTC)
    days = max(0.0, (utc_now() - current.astimezone(UTC)).total_seconds() / 86_400)
    if days <= 7:
        return 1.0
    if days <= 30:
        return 0.8
    if days <= 90:
        return 0.5
    return 0.2


__all__ = [
    "OpportunityCandidate",
    "OpportunityMerge",
    "OpportunityPreferences",
    "OpportunityProvenance",
    "OpportunityRank",
    "canonical_opportunity_url",
    "deduplicate_opportunities",
    "rank_opportunities",
]
