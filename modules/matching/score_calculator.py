"""Code-calculated scoring for Match Engine 2."""

from __future__ import annotations

from modules.matching.confidence import calculate_confidence_score
from modules.matching.domain_weights import DEFAULT_MATCH_WEIGHTS, MatchWeights
from modules.matching.models import CandidateEvidence, MatchScoreBreakdown, RequirementMatch
from modules.matching.risk_adjustment import calculate_risk_penalty
from modules.matching.transferable_skills import TransferableSkillMatch


def calculate_match_scores(
    *,
    matches: list[RequirementMatch],
    evidence: list[CandidateEvidence],
    transferable_skills: list[TransferableSkillMatch],
    domain_fit_score: int = 60,
    seniority_fit_score: int = 60,
    education_credentials_score: int | None = None,
    ats_keyword_alignment_score: int = 60,
    preferences_fit_score: int = 60,
    resume_confidence: float = 0.6,
    job_confidence: float = 0.6,
    weights: MatchWeights | None = None,
) -> MatchScoreBreakdown:
    """Calculate weighted match scores with risk penalties."""
    active_weights = weights or DEFAULT_MATCH_WEIGHTS
    required = _requirement_group_score(
        [match for match in matches if match.requirement.importance == "required"]
    )
    preferred = _requirement_group_score(
        [match for match in matches if match.requirement.importance == "preferred"]
    )
    education = (
        education_credentials_score
        if education_credentials_score is not None
        else _education_credentials_score(matches)
    )
    evidence_strength = _evidence_strength_score(evidence, matches)
    github_portfolio = _github_portfolio_score(evidence)
    risk_penalty = calculate_risk_penalty(matches)
    confidence = calculate_confidence_score(
        matches,
        evidence,
        resume_confidence=resume_confidence,
        job_confidence=job_confidence,
    )
    raw = round(
        required * active_weights.required_requirements
        + preferred * active_weights.preferred_requirements
        + _clamp(domain_fit_score) * active_weights.domain_fit
        + _clamp(seniority_fit_score) * active_weights.seniority_fit
        + _clamp(education) * active_weights.education_credentials
        + evidence_strength * active_weights.evidence_strength
        + github_portfolio * active_weights.portfolio_github_evidence
        + _clamp(ats_keyword_alignment_score) * active_weights.ats_keyword_alignment
        + _clamp(preferences_fit_score) * active_weights.preferences_fit
    )
    overall = _apply_caps(raw - risk_penalty, matches)
    risk_score = _clamp(risk_penalty)
    return MatchScoreBreakdown(
        required_requirements_score=required,
        preferred_requirements_score=preferred,
        domain_fit_score=_clamp(domain_fit_score),
        seniority_fit_score=_clamp(seniority_fit_score),
        education_credentials_score=_clamp(education),
        evidence_strength_score=evidence_strength,
        portfolio_github_evidence_score=github_portfolio,
        ats_keyword_alignment_score=_clamp(ats_keyword_alignment_score),
        preferences_fit_score=_clamp(preferences_fit_score),
        risk_penalty=risk_penalty,
        match_score=overall,
        ats_alignment_score=_clamp(ats_keyword_alignment_score),
        opportunity_fit_score=_clamp(preferences_fit_score),
        evidence_score=evidence_strength,
        risk_score=risk_score,
        confidence_score=confidence,
        overall_score=overall,
    )


def _requirement_group_score(matches: list[RequirementMatch]) -> int:
    if not matches:
        return 100
    values = []
    for match in matches:
        if match.match_status == "matched":
            values.append(100)
        elif match.match_status == "partial":
            values.append(55)
        elif match.match_status == "unclear":
            values.append(35)
        elif match.match_status == "not_applicable":
            values.append(70)
        else:
            values.append(0)
    return round(sum(values) / len(values))


def _education_credentials_score(matches: list[RequirementMatch]) -> int:
    relevant = [
        match
        for match in matches
        if match.requirement.category in {"education", "certification", "professional_license"}
    ]
    return _requirement_group_score(relevant)


def _evidence_strength_score(
    evidence: list[CandidateEvidence],
    matches: list[RequirementMatch],
) -> int:
    if not matches:
        return 30
    matched_evidence = [
        item
        for match in matches
        for item in match.candidate_evidence
        if match.match_status in {"matched", "partial"}
    ]
    if not matched_evidence:
        return 20 if evidence else 10
    strength_values = {"verified": 100, "strong": 85, "medium": 60, "weak": 35, "unclear": 20}
    return round(
        sum(strength_values[item.strength] for item in matched_evidence) / len(matched_evidence)
    )


def _github_portfolio_score(evidence: list[CandidateEvidence]) -> int:
    items = [item for item in evidence if item.evidence_source in {"github", "portfolio"}]
    if not items:
        return 0
    return round(sum(item.confidence * 100 for item in items) / len(items))


def _apply_caps(score: int, matches: list[RequirementMatch]) -> int:
    capped = _clamp(score)
    if any(
        match.gap_severity == "knockout" and match.match_status == "missing" for match in matches
    ):
        capped = min(capped, 45)
    if any(
        match.requirement.category in {"professional_license", "professional_registration"}
        and match.requirement.importance == "required"
        and match.match_status == "missing"
        for match in matches
    ):
        capped = min(capped, 40)
    return capped


def _clamp(value: int) -> int:
    return max(0, min(100, value))
