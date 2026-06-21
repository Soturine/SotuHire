"""Requirement categorization helpers for multi-domain job extraction."""

from __future__ import annotations

from dataclasses import dataclass

from modules.core.text_utils import normalize_text
from modules.domain_intelligence.aliases import normalize_alias


@dataclass(frozen=True)
class RequirementClassification:
    """Deterministic requirement type classification."""

    normalized_name: str
    category: str = "other"
    domain: str = ""
    criticality: str = "medium"
    confidence: float = 0.6


def classify_requirement(text: str) -> RequirementClassification:
    """Classify a requirement into a stable category and normalized name."""
    alias = normalize_alias(text)
    if alias:
        criticality = "knockout" if alias.category == "professional_license" else "high"
        return RequirementClassification(
            normalized_name=alias.normalized_name,
            category=alias.category,
            domain=alias.domain,
            criticality=criticality,
            confidence=alias.confidence,
        )

    normalized = normalize_text(text)
    if any(term in normalized for term in ["graduacao", "bacharel", "licenciatura", "ensino"]):
        return RequirementClassification(text.strip(), "education", criticality="high")
    if any(term in normalized for term in ["certificacao", "certificado"]):
        return RequirementClassification(text.strip(), "certification", criticality="high")
    if any(term in normalized for term in ["ingles", "espanhol", "fluente"]):
        return RequirementClassification(text.strip(), "language", criticality="medium")
    if any(term in normalized for term in ["experiencia", "vivencia", "anos"]):
        return RequirementClassification(text.strip(), "experience", criticality="high")
    if any(term in normalized for term in ["responsavel", "atuar", "realizar", "acompanhar"]):
        return RequirementClassification(text.strip(), "responsibility", criticality="medium")
    if any(term in normalized for term in ["disponibilidade", "plantao", "viagem"]):
        return RequirementClassification(text.strip(), "availability", criticality="high")
    if any(term in normalized for term in ["remoto", "hibrido", "presencial", "local"]):
        return RequirementClassification(text.strip(), "location", criticality="medium")
    if any(term in normalized for term in ["portfolio", "behance", "github"]):
        return RequirementClassification(text.strip(), "portfolio", criticality="medium")
    return RequirementClassification(text.strip())
