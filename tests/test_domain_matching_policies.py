from __future__ import annotations

from modules.matching import policy_for_domain
from modules.matching.domain_weights import CareerDomain

DOMAINS: tuple[CareerDomain, ...] = (
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
)


def test_all_roadmap_domains_have_normalized_deterministic_policies() -> None:
    for domain in DOMAINS:
        policy = policy_for_domain(domain)
        assert policy.domain == domain
        assert abs(policy.weights.total() - 1.0) < 0.0001
        assert policy.applicable_dimensions


def test_counterfactual_irrelevant_attributes_never_change_score() -> None:
    policy = policy_for_domain("healthcare")
    facts = {
        "required_requirements": 80,
        "education_credentials": 100,
        "evidence_strength": 70,
        "portfolio_github_evidence": 0,
        "candidate_name_hash": 1,
        "gender_marker": 1,
    }
    counterfactual = {
        **facts,
        "portfolio_github_evidence": 100,
        "candidate_name_hash": 999,
        "gender_marker": 0,
    }
    assert policy.score(facts) == policy.score(counterfactual)


def test_same_supported_facts_are_order_independent() -> None:
    policy = policy_for_domain("technology")
    first = {"required_requirements": 90, "evidence_strength": 75, "domain_fit": 80}
    second = dict(reversed(list(first.items())))
    assert policy.score(first) == policy.score(second)
