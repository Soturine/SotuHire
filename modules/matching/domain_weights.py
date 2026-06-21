"""Domain-aware weights for Match Engine 2 scoring."""

from __future__ import annotations

from dataclasses import dataclass

from modules.core.text_utils import normalize_text


@dataclass(frozen=True)
class MatchWeights:
    """Weighted contribution of each match dimension."""

    required_requirements: float = 0.30
    preferred_requirements: float = 0.15
    domain_fit: float = 0.10
    seniority_fit: float = 0.10
    education_credentials: float = 0.10
    evidence_strength: float = 0.10
    portfolio_github_evidence: float = 0.05
    ats_keyword_alignment: float = 0.05
    preferences_fit: float = 0.05

    def total(self) -> float:
        """Return the sum of all positive score weights."""
        return sum(
            [
                self.required_requirements,
                self.preferred_requirements,
                self.domain_fit,
                self.seniority_fit,
                self.education_credentials,
                self.evidence_strength,
                self.portfolio_github_evidence,
                self.ats_keyword_alignment,
                self.preferences_fit,
            ]
        )


DEFAULT_MATCH_WEIGHTS = MatchWeights()

DOMAIN_WEIGHT_OVERRIDES: dict[str, MatchWeights] = {
    "nursing": MatchWeights(
        required_requirements=0.30,
        preferred_requirements=0.10,
        domain_fit=0.10,
        seniority_fit=0.08,
        education_credentials=0.17,
        evidence_strength=0.10,
        portfolio_github_evidence=0.00,
        ats_keyword_alignment=0.05,
        preferences_fit=0.10,
    ),
    "healthcare": MatchWeights(
        required_requirements=0.30,
        preferred_requirements=0.10,
        domain_fit=0.10,
        seniority_fit=0.08,
        education_credentials=0.17,
        evidence_strength=0.10,
        portfolio_github_evidence=0.00,
        ats_keyword_alignment=0.05,
        preferences_fit=0.10,
    ),
    "architecture": MatchWeights(
        required_requirements=0.25,
        preferred_requirements=0.12,
        domain_fit=0.10,
        seniority_fit=0.08,
        education_credentials=0.10,
        evidence_strength=0.15,
        portfolio_github_evidence=0.10,
        ats_keyword_alignment=0.05,
        preferences_fit=0.05,
    ),
    "cybersecurity": MatchWeights(
        required_requirements=0.28,
        preferred_requirements=0.12,
        domain_fit=0.10,
        seniority_fit=0.08,
        education_credentials=0.07,
        evidence_strength=0.15,
        portfolio_github_evidence=0.10,
        ats_keyword_alignment=0.05,
        preferences_fit=0.05,
    ),
    "pedagogy": MatchWeights(
        required_requirements=0.28,
        preferred_requirements=0.12,
        domain_fit=0.12,
        seniority_fit=0.08,
        education_credentials=0.17,
        evidence_strength=0.10,
        portfolio_github_evidence=0.00,
        ats_keyword_alignment=0.05,
        preferences_fit=0.08,
    ),
    "engineering": MatchWeights(
        required_requirements=0.30,
        preferred_requirements=0.10,
        domain_fit=0.10,
        seniority_fit=0.08,
        education_credentials=0.15,
        evidence_strength=0.12,
        portfolio_github_evidence=0.05,
        ats_keyword_alignment=0.05,
        preferences_fit=0.05,
    ),
    "civil_engineering": MatchWeights(
        required_requirements=0.30,
        preferred_requirements=0.10,
        domain_fit=0.10,
        seniority_fit=0.08,
        education_credentials=0.15,
        evidence_strength=0.12,
        portfolio_github_evidence=0.05,
        ats_keyword_alignment=0.05,
        preferences_fit=0.05,
    ),
}

DOMAIN_ALIASES = {
    "enfermagem": "nursing",
    "saude": "healthcare",
    "arquitetura": "architecture",
    "engenharia": "engineering",
    "engenharia civil": "civil_engineering",
    "pedagogia": "pedagogy",
    "educacao": "pedagogy",
    "seguranca da informacao": "cybersecurity",
    "cyber security": "cybersecurity",
}


def weights_for_domain(domain: str) -> MatchWeights:
    """Return a stable domain-specific weight profile."""
    normalized = normalize_text(domain).replace("_", " ")
    canonical = DOMAIN_ALIASES.get(normalized, normalized.replace(" ", "_"))
    return DOMAIN_WEIGHT_OVERRIDES.get(canonical, DEFAULT_MATCH_WEIGHTS)
