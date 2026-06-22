"""Extraction and analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.routes.responses import ok
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
from apps.api.schemas.common import ApiEnvelope
from apps.api.services.analysis import (
    analyze_ats,
    analyze_github_repo,
    analyze_match,
    extract_job,
    extract_resume,
    tailor_resume,
)

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/resume/extract", response_model=ApiEnvelope[ResumeExtractResponse])
def resume_extract(payload: ResumeExtractRequest) -> ApiEnvelope[ResumeExtractResponse]:
    """Extract a structured resume profile."""
    data, warnings = extract_resume(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/job/extract", response_model=ApiEnvelope[JobExtractResponse])
def job_extract(payload: JobExtractRequest) -> ApiEnvelope[JobExtractResponse]:
    """Extract a structured job posting."""
    data, warnings = extract_job(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/match/analyze", response_model=ApiEnvelope[MatchAnalyzeResponse])
def match_analyze(payload: MatchAnalyzeRequest) -> ApiEnvelope[MatchAnalyzeResponse]:
    """Analyze candidate/job match."""
    data, warnings = analyze_match(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/ats/analyze", response_model=ApiEnvelope[AtsAnalyzeResponse])
def ats_analyze(payload: AtsAnalyzeRequest) -> ApiEnvelope[AtsAnalyzeResponse]:
    """Review ATS keywords."""
    data, warnings = analyze_ats(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/resume/tailor", response_model=ApiEnvelope[ResumeTailorResponse])
def resume_tailor(payload: ResumeTailorRequest) -> ApiEnvelope[ResumeTailorResponse]:
    """Build safe resume-tailoring suggestions."""
    data, warnings = tailor_resume(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/github/repo/analyze", response_model=ApiEnvelope[GitHubRepoAnalyzeResponse])
def github_repo_analyze(
    payload: GitHubRepoAnalyzeRequest,
) -> ApiEnvelope[GitHubRepoAnalyzeResponse]:
    """Analyze a public GitHub repository."""
    data, warnings = analyze_github_repo(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)
