"""Deterministic Match Engine 2 orchestration."""

from __future__ import annotations

from modules.ai.schemas.job_extraction import JobExtractionOutput
from modules.ai.schemas.resume_extraction import ResumeExtractionOutput
from modules.core.text_utils import normalize_text
from modules.github_analyzer.schemas import GitHubAnalyzerReport
from modules.matching.evidence_matcher import (
    collect_github_evidence,
    collect_portfolio_evidence,
    collect_resume_evidence,
    collect_text_evidence,
    combine_evidence,
)
from modules.matching.explanation_builder import build_match_explanation
from modules.matching.models import (
    MatchRequirement,
    MatchResultV2,
    RecommendationAction,
)
from modules.matching.requirement_matcher import (
    match_requirements,
    normalize_requirement,
    requirements_from_job_extraction,
)
from modules.matching.risk_adjustment import build_critical_gaps
from modules.matching.score_calculator import calculate_match_scores
from modules.matching.transferable_skills import find_transferable_skills
from modules.portfolio.schemas import ProjectAnalysisReport


def analyze_match_v2(
    *,
    resume: ResumeExtractionOutput,
    job: JobExtractionOutput,
    github_report: GitHubAnalyzerReport | None = None,
    portfolio_report: ProjectAnalysisReport | None = None,
    memory_items: list[str] | None = None,
    profile_items: list[str] | None = None,
    preferences_fit_score: int = 60,
) -> MatchResultV2:
    """Run Match Engine 2 without calling external AI."""
    requirements = _requirements(job)
    evidence = combine_evidence(
        collect_resume_evidence(resume),
        collect_github_evidence(github_report),
        collect_portfolio_evidence(portfolio_report),
        collect_text_evidence(memory_items or [], source="memory"),
        collect_text_evidence(profile_items or [], source="profile"),
    )
    matches = match_requirements(requirements, evidence)
    transferable = find_transferable_skills(evidence, requirements)
    critical_gaps = build_critical_gaps(matches)
    scores = calculate_match_scores(
        matches=matches,
        evidence=evidence,
        transferable_skills=transferable,
        domain_fit_score=_domain_fit(resume, job),
        seniority_fit_score=_seniority_fit(resume, job),
        ats_keyword_alignment_score=_ats_alignment(job, evidence),
        preferences_fit_score=preferences_fit_score,
        resume_confidence=resume.extraction_confidence.overall or 0.55,
        job_confidence=job.extraction_confidence.overall or 0.55,
    )
    explanation = build_match_explanation(
        matches=matches,
        critical_gaps=critical_gaps,
        transferable_skills=transferable,
        scores=scores,
    )
    return MatchResultV2(
        requirements=requirements,
        requirement_matches=matches,
        critical_gaps=critical_gaps,
        transferable_skills=transferable,
        score_breakdown=scores,
        explanation=explanation,
        recommendation=_recommendation(scores.overall_score, scores.risk_score),
        fallback_used=False,
        provider_used="local",
    )


def _requirements(job: JobExtractionOutput) -> list[MatchRequirement]:
    requirements = requirements_from_job_extraction(job)
    if requirements:
        return requirements
    return [
        normalize_requirement(keyword, importance="preferred", criticality="medium")
        for keyword in job.keywords_for_ats[:20]
    ]


def _domain_fit(resume: ResumeExtractionOutput, job: JobExtractionOutput) -> int:
    job_domain = job.domain_classification.primary_domain
    resume_domains = {item.domain for item in resume.domains}
    if not job_domain or job_domain == "unknown":
        return 55
    if job_domain in resume_domains:
        return 90
    if resume_domains & set(job.domain_classification.secondary_domains):
        return 75
    if not resume_domains:
        return 45
    return 55


def _seniority_fit(resume: ResumeExtractionOutput, job: JobExtractionOutput) -> int:
    job_level = job.seniority.level
    resume_level = resume.seniority.estimated_level
    if "unknown" in {job_level, resume_level}:
        return 55
    order = {
        "intern": 1,
        "apprentice": 1,
        "assistant": 2,
        "junior": 3,
        "mid": 4,
        "senior": 5,
        "specialist": 6,
        "coordinator": 6,
        "manager": 7,
        "director": 8,
    }
    diff = order.get(resume_level, 0) - order.get(job_level, 0)
    if diff >= 0:
        return 90
    if diff == -1:
        return 65
    return 35


def _ats_alignment(job: JobExtractionOutput, evidence) -> int:
    keywords = [normalize_text(keyword) for keyword in job.keywords_for_ats if keyword]
    if not keywords:
        return 60
    corpus = normalize_text(" ".join(f"{item.skill} {item.evidence_text}" for item in evidence))
    matched = sum(1 for keyword in keywords if keyword in corpus)
    return round((matched / len(keywords)) * 100)


def _recommendation(overall: int, risk_score: int) -> RecommendationAction:
    if risk_score >= 55 or overall < 40:
        return "ignore"
    if overall >= 80:
        return "apply"
    if overall >= 60:
        return "apply_with_adjustments"
    return "save_for_later"
