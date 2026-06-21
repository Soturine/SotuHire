"""Deterministic professional domain classifier."""

from __future__ import annotations

import re

from modules.ai.schemas.common import DomainSignal
from modules.ai.schemas.domain_classification import (
    AliasDetection,
    DomainClassificationOutput,
    RegulatedProfessionSignal,
)
from modules.core.text_utils import normalize_text
from modules.domain_intelligence.aliases import AliasEntry, find_aliases
from modules.domain_intelligence.domain_catalog import DOMAIN_RULES, PROFESSIONAL_DOMAINS


def classify_domain(
    text: str,
    *,
    text_type: str = "job",
    known_context: dict[str, object] | None = None,
) -> DomainClassificationOutput:
    """Classify professional domain from text using conservative deterministic rules."""
    normalized = normalize_text(text)
    if not normalized:
        return DomainClassificationOutput(
            primary_domain=DomainSignal(domain="unknown", confidence=0.0),
            domain_notes=["Empty text."],
            needs_review=True,
        )

    aliases = find_aliases(text)
    scores: dict[str, int] = {domain: 0 for domain in PROFESSIONAL_DOMAINS}
    evidence: dict[str, list[str]] = {domain: [] for domain in PROFESSIONAL_DOMAINS}

    for rule in DOMAIN_RULES:
        for keyword in rule.keywords:
            if _contains(normalized, keyword):
                scores[rule.name] += 1
                evidence[rule.name].append(keyword)

    for alias, entry in aliases.items():
        domain = _coerce_domain(entry.domain)
        scores[domain] += 2 if entry.category == "professional_license" else 1
        evidence[domain].append(entry.normalized_name)

    primary_domain, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score <= 0:
        primary = DomainSignal(domain="unknown", confidence=0.2, evidence=[])
    else:
        primary = DomainSignal(
            domain=primary_domain,
            confidence=min(0.95, 0.4 + best_score * 0.12),
            evidence=list(dict.fromkeys(evidence[primary_domain]))[:8],
        )

    secondary = [
        DomainSignal(
            domain=domain,
            confidence=min(0.9, 0.35 + score * 0.1),
            evidence=list(dict.fromkeys(evidence[domain]))[:5],
        )
        for domain, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
        if domain != primary.domain and score > 0
    ][:5]

    alias_detections = [_alias_detection(alias, entry) for alias, entry in aliases.items()]
    regulated = [
        RegulatedProfessionSignal(
            credential=entry.normalized_name,
            domain=_coerce_domain(entry.domain),
            evidence=alias,
            confidence=entry.confidence,
        )
        for alias, entry in aliases.items()
        if entry.category == "professional_license"
    ]
    categories = sorted({item.category for item in alias_detections})
    if primary.domain in {"unknown", "general"}:
        categories.append("other")

    notes = []
    if known_context:
        notes.append("Known context was provided but deterministic classification used text evidence.")
    if text_type not in {"resume", "job", "project", "profile", "post"}:
        notes.append(f"Unrecognized text_type: {text_type}.")

    return DomainClassificationOutput(
        primary_domain=primary,
        secondary_domains=secondary,
        requirement_categories_detected=list(dict.fromkeys(categories)),
        regulated_profession_signals=regulated,
        aliases_detected=alias_detections,
        domain_notes=notes,
        needs_review=primary.confidence < 0.7,
    )


def _contains(normalized_text: str, keyword: str) -> bool:
    normalized_keyword = normalize_text(keyword)
    return bool(re.search(rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)", normalized_text))


def _coerce_domain(domain: str) -> str:
    return domain if domain in PROFESSIONAL_DOMAINS else "general"


def _alias_detection(alias: str, entry: AliasEntry) -> AliasDetection:
    return AliasDetection(
        original=alias,
        normalized_name=entry.normalized_name,
        category=entry.category,
        domain=_coerce_domain(entry.domain),
        evidence=alias,
        confidence=entry.confidence,
    )
