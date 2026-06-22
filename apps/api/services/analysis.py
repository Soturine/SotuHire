"""Thin service layer over existing SotuHire domain modules."""

from __future__ import annotations

from fastapi import HTTPException
from modules.ai.providers import MockProvider
from modules.ai.structured_analysis import analyze_structured
from modules.ats.match_keywords import review_keywords_with_match
from modules.github_analyzer.analyzer_service import analyze_github_repository
from modules.github_analyzer.exceptions import GitHubAnalyzerError
from modules.parsers.job_description_parser import parse_job_description
from modules.parsers.resume_parser import parse_resume_text
from modules.resume_tailor.tailor_rules import build_safe_tailor_output
from modules.schemas.job_posting import JobPostingSchema
from modules.schemas.resume_profile import ResumeProfileSchema

from apps.api.schemas.analysis import (
    AtsAnalyzeRequest,
    AtsAnalyzeResponse,
    GitHubRepoAnalyzeRequest,
    GitHubRepoAnalyzeResponse,
    JobExtractRequest,
    JobExtractResponse,
    MatchAnalyzeRequest,
    MatchAnalyzeResponse,
    ResumeExtractRequest,
    ResumeExtractResponse,
    ResumeTailorRequest,
    ResumeTailorResponse,
)


def extract_resume(request: ResumeExtractRequest) -> tuple[ResumeExtractResponse, list[str]]:
    """Parse a resume and return warnings separately for the API envelope."""
    profile = parse_resume_text(request.resume_text, source_type=request.source_type)
    warnings: list[str] = []
    if not profile.skills and not profile.experiences:
        warnings.append("Poucas evidencias estruturadas foram detectadas no curriculo.")
    if not request.include_raw_text:
        profile = profile.model_copy(update={"raw_text": ""})
    return ResumeExtractResponse(profile=profile, confidence=_resume_confidence(profile)), warnings


def extract_job(request: JobExtractRequest) -> tuple[JobExtractResponse, list[str]]:
    """Parse a job description and return warnings separately for the API envelope."""
    job = parse_job_description(request.job_text)
    if not request.include_raw_text:
        job = job.model_copy(update={"raw_text": ""})
    return JobExtractResponse(job=job, confidence=_job_confidence(job)), list(job.risk_flags)


def analyze_match(request: MatchAnalyzeRequest) -> tuple[MatchAnalyzeResponse, list[str]]:
    """Run the local structured analysis path."""
    resume_text = request.resume_text.strip() or _profile_to_text(request.profile)
    job_text = request.job_text.strip() or _job_to_text(request.job)
    if not resume_text:
        raise HTTPException(status_code=422, detail="Envie resume_text ou profile.")
    if not job_text:
        raise HTTPException(status_code=422, detail="Envie job_text ou job.")
    resume_text = _append_evidence(
        resume_text,
        github_evidence=request.github_evidence,
        portfolio_evidence=request.portfolio_evidence,
    )
    result = analyze_structured(
        resume_text,
        job_text,
        preferences=request.preferences,
        job_details=(request.job.model_dump() if request.job else None),
        provider=MockProvider(),
    )
    warnings = [result.warning] if result.warning else []
    return (
        MatchAnalyzeResponse(
            analysis=result.analysis,
            provider_used=result.provider,
            local_first=True,
        ),
        warnings,
    )


def analyze_ats(request: AtsAnalyzeRequest) -> tuple[AtsAnalyzeResponse, list[str]]:
    """Classify ATS keywords using match evidence."""
    analysis = request.match_analysis
    warnings: list[str] = []
    if analysis is None:
        match_response, match_warnings = analyze_match(
            MatchAnalyzeRequest(resume_text=request.resume_text, job_text=request.job_text)
        )
        analysis = match_response.analysis
        warnings.extend(match_warnings)
    keywords = _unique(request.job_keywords)
    if not keywords and request.job_text.strip():
        keywords = parse_job_description(request.job_text).ats_keywords
    if not keywords:
        keywords = _unique(
            [
                *analysis.matched_requirements,
                *analysis.partial_requirements,
                *analysis.missing_requirements,
                *analysis.missing_keywords,
            ]
        )
    review = review_keywords_with_match(analysis, keywords)
    return (
        AtsAnalyzeResponse(
            ats_score=analysis.ats_score,
            present=review.present,
            missing_but_safe_to_add_if_true=review.missing_but_safe_to_add_if_true,
            missing_without_evidence=review.missing_without_evidence,
        ),
        warnings,
    )


def tailor_resume(request: ResumeTailorRequest) -> tuple[ResumeTailorResponse, list[str]]:
    """Build safe, evidence-backed tailoring suggestions."""
    tailor = build_safe_tailor_output(
        target_role=request.target_role,
        target_company=request.target_company,
        job_text=request.job_text,
        evidence_text=request.evidence_text,
        match_analysis=request.match_analysis,
    )
    return ResumeTailorResponse(tailor=tailor, safe_to_export=tailor.is_safe_to_export()), list(
        tailor.warnings
    )


def analyze_github_repo(
    request: GitHubRepoAnalyzeRequest,
) -> tuple[GitHubRepoAnalyzeResponse, list[str]]:
    """Analyze a public GitHub repository through the existing analyzer."""
    try:
        report = analyze_github_repository(
            request.repo_url,
            analysis_input=request.to_analysis_input(),
            fallback_payload=request.fallback_payload,
        )
    except GitHubAnalyzerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    warnings = ["Analise GitHub usou fallback local."] if report.fallback_used else []
    return GitHubRepoAnalyzeResponse(report=report), warnings


def _resume_confidence(profile: ResumeProfileSchema) -> float:
    signals = [
        bool(profile.name),
        bool(profile.email),
        bool(profile.summary),
        bool(profile.skills),
        bool(profile.experiences),
        bool(profile.projects),
        bool(profile.education),
    ]
    return round(min(0.95, 0.25 + (sum(signals) * 0.1)), 2)


def _job_confidence(job: JobPostingSchema) -> float:
    signals = [
        bool(job.title),
        bool(job.company),
        bool(job.required_skills),
        bool(job.ats_keywords),
        job.modality != "unknown",
        bool(job.contract),
        bool(job.seniority),
    ]
    return round(min(0.95, 0.3 + (sum(signals) * 0.09)), 2)


def _profile_to_text(profile: ResumeProfileSchema | None) -> str:
    if profile is None:
        return ""
    sections = [
        profile.name,
        profile.summary,
        "Skills: " + ", ".join(profile.skills),
        "Experiencias: " + "\n".join(profile.experiences),
        "Projetos: " + "\n".join(profile.projects),
        "Formacao: " + "\n".join(profile.education),
        "Links: " + ", ".join(profile.links),
        profile.raw_text,
    ]
    return "\n".join(section for section in sections if section.strip())


def _job_to_text(job: JobPostingSchema | None) -> str:
    if job is None:
        return ""
    sections = [
        job.title,
        job.company,
        job.location,
        job.modality,
        job.contract,
        job.seniority,
        "Obrigatorios: " + ", ".join(job.required_skills),
        "Desejaveis: " + ", ".join(job.desired_skills),
        "ATS: " + ", ".join(job.ats_keywords),
        job.raw_text,
    ]
    return "\n".join(section for section in sections if section.strip())


def _append_evidence(
    resume_text: str,
    *,
    github_evidence: list[str],
    portfolio_evidence: list[str],
) -> str:
    evidence = _unique([*github_evidence, *portfolio_evidence])
    if not evidence:
        return resume_text
    return f"{resume_text}\n\nEvidencias publicas fornecidas:\n" + "\n".join(evidence)


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))
