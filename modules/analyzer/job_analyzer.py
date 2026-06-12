"""Integrated deterministic analysis for the SotuHire v0.1 MVP."""

from __future__ import annotations

from modules.analyzer.recommendation import (
    build_recommendation,
    calculate_risk_score,
    detect_risk_flags,
)
from modules.ats.ats_score import calculate_simple_ats_score
from modules.core.text_utils import extract_keywords, first_sentences, keyword_coverage
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
