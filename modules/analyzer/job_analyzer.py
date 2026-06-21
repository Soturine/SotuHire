"""Integrated deterministic analysis for the SotuHire v0.1 MVP."""

from __future__ import annotations

from modules.ai.schemas.job_extraction import JobExtractionOutput
from modules.ai.schemas.resume_extraction import ResumeExtractionOutput
from modules.analyzer.recommendation import (
    build_recommendation,
    calculate_risk_score,
    detect_risk_flags,
)
from modules.ats.ats_score import calculate_simple_ats_score
from modules.core.text_utils import extract_keywords, first_sentences, keyword_coverage
from modules.github_analyzer.schemas import GitHubAnalyzerReport
from modules.matching.models import MatchResultV2
from modules.portfolio.schemas import ProjectAnalysisReport
from modules.preferences.opportunity_fit import calculate_opportunity_fit_score
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


def detect_missing_keywords(resume_text: str, job_text: str, limit: int = 15) -> list[str]:
    """Return job keywords that are absent from the supplied resume."""
    resume_keywords = set(extract_keywords(resume_text, limit=200))
    return [keyword for keyword in extract_keywords(job_text) if keyword not in resume_keywords][
        :limit
    ]


def detect_strengths(resume_text: str, job_text: str, limit: int = 8) -> list[str]:
    """Return evidence-backed strengths shared by resume and job text."""
    resume_keywords = set(extract_keywords(resume_text, limit=200))
    common = [keyword for keyword in extract_keywords(job_text) if keyword in resume_keywords]
    return [f"Evidencia encontrada para: {keyword}" for keyword in common[:limit]]


def build_tailored_summary(resume_text: str, job_text: str) -> str:
    """Build a short summary using only sentences from the supplied resume."""
    job_keywords = set(extract_keywords(job_text))
    sentences = first_sentences(resume_text, limit=8)
    relevant = [
        sentence
        for sentence in sentences
        if job_keywords.intersection(extract_keywords(sentence, limit=50))
    ]
    selected = relevant[:2] or sentences[:2]
    return " ".join(selected)


def analyze_job(
    resume_text: str,
    job_text: str,
    preferences: UserPreferences | None = None,
    job_details: dict[str, object] | None = None,
) -> JobAnalysisSchema:
    """Analyze pasted resume and job text with deterministic MVP rules."""
    preferences = preferences or UserPreferences()
    job_details = job_details or {}

    match_score = keyword_coverage(job_text, resume_text)
    ats_score = calculate_simple_ats_score(resume_text, job_text)
    opportunity_fit_score = calculate_opportunity_fit_score(job_details, preferences)
    risk_flags = detect_risk_flags(job_text, resume_text)
    risk_score = calculate_risk_score(risk_flags)
    missing_keywords = detect_missing_keywords(resume_text, job_text)
    strengths = detect_strengths(resume_text, job_text)

    if not strengths and resume_text.strip():
        strengths = ["Curriculo fornecido e disponivel para revisao direcionada."]

    return JobAnalysisSchema(
        match_score=match_score,
        ats_score=ats_score,
        opportunity_fit_score=opportunity_fit_score,
        risk_score=risk_score,
        recommendation=build_recommendation(
            match_score=match_score,
            ats_score=ats_score,
            opportunity_fit_score=opportunity_fit_score,
            risk_score=risk_score,
        ),
        strengths=strengths,
        gaps=[f"Keyword ausente: {keyword}" for keyword in missing_keywords[:8]],
        missing_keywords=missing_keywords,
        risk_flags=risk_flags,
        tailored_summary=build_tailored_summary(resume_text, job_text),
    )


def analyze_job_v2(
    resume: ResumeExtractionOutput,
    job: JobExtractionOutput,
    *,
    github_report: GitHubAnalyzerReport | None = None,
    portfolio_report: ProjectAnalysisReport | None = None,
    memory_items: list[str] | None = None,
    profile_items: list[str] | None = None,
    preferences_fit_score: int = 60,
    fallback_resume_text: str = "",
    fallback_job_text: str = "",
) -> JobAnalysisSchema:
    """Analyze structured resume/job data through Match Engine 2 with legacy fallback."""
    try:
        from modules.matching.engine import analyze_match_v2

        result = analyze_match_v2(
            resume=resume,
            job=job,
            github_report=github_report,
            portfolio_report=portfolio_report,
            memory_items=memory_items,
            profile_items=profile_items,
            preferences_fit_score=preferences_fit_score,
        )
        return job_analysis_from_match_v2(result)
    except Exception:
        return analyze_job(fallback_resume_text, fallback_job_text)


def job_analysis_from_match_v2(result: MatchResultV2) -> JobAnalysisSchema:
    """Convert Match Engine 2 output to the existing JobAnalysisSchema contract."""
    scores = result.score_breakdown
    explanation = result.explanation
    missing_without_evidence = [
        match.requirement.requirement_text
        for match in result.requirement_matches
        if match.match_status == "missing"
    ]
    safe_to_add_if_true = [
        match.requirement.requirement_text
        for match in result.requirement_matches
        if match.match_status == "partial" and match.requirement.category != "professional_license"
    ]
    return JobAnalysisSchema(
        match_score=scores.match_score,
        ats_score=scores.ats_alignment_score,
        opportunity_fit_score=scores.opportunity_fit_score,
        risk_score=scores.risk_score,
        recommendation=result.recommendation,
        strengths=explanation.matched_requirements[:8],
        gaps=[*explanation.critical_gaps, *explanation.missing_requirements][:8],
        missing_keywords=explanation.missing_requirements[:15],
        risk_flags=explanation.critical_gaps,
        tailored_summary=explanation.summary,
        recruiter_message=" ".join(explanation.safe_actions[:2]),
        analysis_version="match_engine_v2",
        confidence_score=scores.confidence_score,
        evidence_score=scores.evidence_score,
        matched_requirements=explanation.matched_requirements,
        partial_requirements=explanation.partial_requirements,
        missing_requirements=explanation.missing_requirements,
        critical_gaps=explanation.critical_gaps,
        transferable_skills=explanation.transferable_skills,
        evidence_used=explanation.evidence_used,
        safe_actions=explanation.safe_actions,
        resume_improvements=explanation.resume_improvements,
        portfolio_github_improvements=explanation.portfolio_github_improvements,
        score_reasoning=explanation.score_reasoning,
        ats_present_keywords=explanation.matched_requirements,
        ats_missing_but_safe_to_add=safe_to_add_if_true,
        ats_missing_without_evidence=missing_without_evidence,
    )
