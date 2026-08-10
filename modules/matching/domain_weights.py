"""Domain-aware weights for Match Engine 2 scoring."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

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

CareerDomain = Literal[
    "technology",
    "engineering",
    "healthcare",
    "education",
    "law",
    "research",
    "administration",
    "finance",
    "design",
    "tourism_services",
    "public_exams",
    "early_career",
    "career_transition",
]


@dataclass(frozen=True)
class DomainMatchingPolicy:
    """Deterministic applicability and weights for one broad career domain."""

    domain: CareerDomain
    weights: MatchWeights
    applicable_dimensions: frozenset[str]
    rationale: str

    def score(self, dimensions: Mapping[str, float]) -> float:
        """Score only named applicable dimensions; unrelated attributes cannot influence it."""
        weighted = {
            "required_requirements": self.weights.required_requirements,
            "preferred_requirements": self.weights.preferred_requirements,
            "domain_fit": self.weights.domain_fit,
            "seniority_fit": self.weights.seniority_fit,
            "education_credentials": self.weights.education_credentials,
            "evidence_strength": self.weights.evidence_strength,
            "portfolio_github_evidence": self.weights.portfolio_github_evidence,
            "ats_keyword_alignment": self.weights.ats_keyword_alignment,
            "preferences_fit": self.weights.preferences_fit,
        }
        denominator = sum(
            weight
            for name, weight in weighted.items()
            if name in self.applicable_dimensions and weight > 0
        )
        if denominator <= 0:
            return 0.0
        numerator = sum(
            min(100.0, max(0.0, float(dimensions.get(name, 0.0)))) * weight
            for name, weight in weighted.items()
            if name in self.applicable_dimensions and weight > 0
        )
        return round(numerator / denominator, 2)


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

_ALL_DIMENSIONS = frozenset(
    {
        "required_requirements",
        "preferred_requirements",
        "domain_fit",
        "seniority_fit",
        "education_credentials",
        "evidence_strength",
        "portfolio_github_evidence",
        "ats_keyword_alignment",
        "preferences_fit",
    }
)

_DOMAIN_GROUPS: dict[str, CareerDomain] = {
    "software_engineering": "technology",
    "cybersecurity": "technology",
    "data": "technology",
    "qa": "technology",
    "technology": "technology",
    "engineering": "engineering",
    "civil_engineering": "engineering",
    "electrical_engineering": "engineering",
    "mechanical_engineering": "engineering",
    "biomedical_engineering": "engineering",
    "healthcare": "healthcare",
    "nursing": "healthcare",
    "psychology": "healthcare",
    "education": "education",
    "pedagogy": "education",
    "law": "law",
    "research": "research",
    "administration": "administration",
    "business": "administration",
    "logistics": "administration",
    "finance": "finance",
    "design": "design",
    "architecture": "design",
    "interior_design": "design",
    "tourism": "tourism_services",
    "services": "tourism_services",
    "tourism_services": "tourism_services",
    "public_exams": "public_exams",
    "early_career": "early_career",
    "career_transition": "career_transition",
}


def _policy_weights(domain: CareerDomain) -> MatchWeights:
    if domain in {"healthcare", "law", "engineering", "education", "public_exams"}:
        return MatchWeights(
            required_requirements=0.30,
            preferred_requirements=0.08,
            domain_fit=0.10,
            seniority_fit=0.07,
            education_credentials=0.20,
            evidence_strength=0.12,
            portfolio_github_evidence=0.00,
            ats_keyword_alignment=0.05,
            preferences_fit=0.08,
        )
    if domain in {"technology", "design", "research"}:
        return MatchWeights(
            required_requirements=0.27,
            preferred_requirements=0.10,
            domain_fit=0.10,
            seniority_fit=0.08,
            education_credentials=0.07,
            evidence_strength=0.18,
            portfolio_github_evidence=0.10,
            ats_keyword_alignment=0.05,
            preferences_fit=0.05,
        )
    if domain == "early_career":
        return MatchWeights(
            required_requirements=0.22,
            preferred_requirements=0.08,
            domain_fit=0.10,
            seniority_fit=0.05,
            education_credentials=0.15,
            evidence_strength=0.18,
            portfolio_github_evidence=0.10,
            ats_keyword_alignment=0.05,
            preferences_fit=0.07,
        )
    if domain == "career_transition":
        return MatchWeights(
            required_requirements=0.22,
            preferred_requirements=0.08,
            domain_fit=0.10,
            seniority_fit=0.05,
            education_credentials=0.08,
            evidence_strength=0.25,
            portfolio_github_evidence=0.08,
            ats_keyword_alignment=0.05,
            preferences_fit=0.09,
        )
    return DEFAULT_MATCH_WEIGHTS


def policy_for_domain(domain: str) -> DomainMatchingPolicy:
    """Return a broad, reviewable policy without consulting a generative model."""
    normalized = normalize_text(domain).replace(" ", "_")
    broad = _DOMAIN_GROUPS.get(normalized, "administration")
    applicable = _ALL_DIMENSIONS
    if broad in {"healthcare", "law", "education", "public_exams"}:
        applicable = applicable - {"portfolio_github_evidence"}
    return DomainMatchingPolicy(
        domain=broad,
        weights=_policy_weights(broad),
        applicable_dimensions=frozenset(applicable),
        rationale=(
            "Pesos determinísticos por domínio; dimensões não aplicáveis são removidas e "
            "o score é renormalizado. A política não usa atributos pessoais."
        ),
    )


def weights_for_domain(domain: str) -> MatchWeights:
    """Return a stable domain-specific weight profile."""
    normalized = normalize_text(domain).replace("_", " ")
    canonical = DOMAIN_ALIASES.get(normalized, normalized.replace(" ", "_"))
    return DOMAIN_WEIGHT_OVERRIDES.get(canonical, policy_for_domain(canonical).weights)
