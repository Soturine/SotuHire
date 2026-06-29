"""Thin service layer over existing SotuHire domain modules."""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.schemas.analysis_insights import AtsAiReviewOutput, ResumeTailorAiOutput
from modules.ai.structured_analysis import analyze_structured
from modules.ai.structured_job_extractor import extract_structured_job
from modules.ai.structured_resume_extractor import extract_structured_resume
from modules.ats.match_keywords import review_keywords_with_match
from modules.github_analyzer.analyzer_service import analyze_github_repository
from modules.github_analyzer.exceptions import GitHubAnalyzerError
from modules.parsers.job_description_parser import parse_job_description
from modules.parsers.resume_parser import parse_resume_text
from modules.profile import ProfileContextOrchestrator
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
from apps.api.services.ai_settings import get_ai_runtime


def extract_resume(request: ResumeExtractRequest) -> tuple[ResumeExtractResponse, list[str]]:
    """Parse a resume and return warnings separately for the API envelope."""
    runtime = get_ai_runtime("resume")
    warnings = list(runtime.warnings)
    low_confidence: list[str] = []
    provider_used = runtime.provider_name
    requested_provider = runtime.requested_provider
    fallback_used = runtime.fallback_used

    if runtime.use_ai and runtime.provider_name != "local":
        result = extract_structured_resume(
            request.resume_text,
            file_type=request.source_type,
            provider=runtime.provider,
        )
        profile = result.local_profile
        provider_used = result.provider
        requested_provider = result.requested_provider
        fallback_used = result.fallback_used
        low_confidence = result.low_confidence_fields
        if result.warning:
            warnings.append(_safe_provider_warning("Curriculo", result.warning))
    else:
        profile = parse_resume_text(request.resume_text, source_type=request.source_type)

    if not profile.skills and not profile.experiences:
        warnings.append("Poucas evidencias estruturadas foram detectadas no curriculo.")
    if not request.include_raw_text:
        profile = profile.model_copy(update={"raw_text": ""})
    return (
        ResumeExtractResponse(
            profile=profile,
            confidence=_resume_confidence(profile),
            provider_used=provider_used,
            requested_provider=str(requested_provider),
            analysis_mode=_analysis_mode(provider_used, fallback_used),
            fallback_used=fallback_used,
            low_confidence_fields=low_confidence,
        ),
        warnings,
    )


def extract_job(request: JobExtractRequest) -> tuple[JobExtractResponse, list[str]]:
    """Parse a job description and return warnings separately for the API envelope."""
    runtime = get_ai_runtime("job")
    warnings = list(runtime.warnings)
    low_confidence: list[str] = []
    provider_used = runtime.provider_name
    requested_provider = runtime.requested_provider
    fallback_used = runtime.fallback_used

    if runtime.use_ai and runtime.provider_name != "local":
        result = extract_structured_job(
            request.job_text,
            source={"url": request.source_url} if request.source_url else {},
            provider=runtime.provider,
        )
        job = result.local_job
        provider_used = result.provider
        requested_provider = result.requested_provider
        fallback_used = result.fallback_used
        low_confidence = result.low_confidence_fields
        if result.warning:
            warnings.append(_safe_provider_warning("Vaga", result.warning))
    else:
        job = parse_job_description(request.job_text)

    if not request.include_raw_text:
        job = job.model_copy(update={"raw_text": ""})
    warnings.extend(job.risk_flags)
    return (
        JobExtractResponse(
            job=job,
            confidence=_job_confidence(job),
            provider_used=provider_used,
            requested_provider=str(requested_provider),
            analysis_mode=_analysis_mode(provider_used, fallback_used),
            fallback_used=fallback_used,
            low_confidence_fields=low_confidence,
        ),
        warnings,
    )


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
    runtime = get_ai_runtime("match")
    profile_context_text = _profile_context_text()
    profile_context_applied = bool(profile_context_text) and (
        runtime.provider_name == "local" or runtime.allow_memory_context
    )
    if profile_context_applied:
        resume_text = _append_profile_context(resume_text, profile_context_text)
    result = analyze_structured(
        resume_text,
        job_text,
        preferences=request.preferences,
        job_details=(request.job.model_dump() if request.job else None),
        provider=runtime.provider,
        share_memory_with_provider=runtime.allow_memory_context,
    )
    warnings = [*runtime.warnings, *([result.warning] if result.warning else [])]
    if profile_context_applied:
        warnings.append("Contexto do Perfil Profissional aplicado como evidencia.")
    elif profile_context_text and runtime.provider_name != "local":
        warnings.append("Contexto do perfil nao foi enviado ao provider externo.")
    return (
        MatchAnalyzeResponse(
            analysis=result.analysis,
            provider_used=result.provider,
            requested_provider=result.requested_provider,
            analysis_mode=_analysis_mode(result.provider, result.fallback_used),
            fallback_used=result.fallback_used,
            local_first=result.provider == "local",
            model=result.model,
            memory_shared_with_provider=result.memory_shared_with_provider,
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
    runtime = get_ai_runtime("ats")
    warnings.extend(runtime.warnings)
    provider_used = runtime.provider_name
    fallback_used = runtime.fallback_used
    ai_insights: list[str] = []

    if runtime.use_ai and runtime.provider_name != "local":
        try:
            spec = default_prompt_registry().get("ats_analysis_v1")
            output = runtime.provider.generate_structured(
                spec,
                {
                    "resume_text": request.resume_text,
                    "job_text": request.job_text,
                    "keywords": keywords,
                    "deterministic_review": {
                        "ats_score": analysis.ats_score,
                        "present": review.present,
                        "missing_but_safe_to_add_if_true": review.missing_but_safe_to_add_if_true,
                        "missing_without_evidence": review.missing_without_evidence,
                    },
                    "language": "pt-BR",
                },
            )
            ai_review = AtsAiReviewOutput.model_validate(output)
            ai_insights = _unique(
                [
                    *ai_review.keyword_observations,
                    *ai_review.safe_to_add_if_true,
                ]
            )[:8]
            warnings.extend(ai_review.warnings)
        except Exception:
            provider_used = "local"
            fallback_used = True
            warnings.append("Gemini falhou na Analise ATS; mantive a revisao local.")

    return (
        AtsAnalyzeResponse(
            ats_score=analysis.ats_score,
            present=review.present,
            missing_but_safe_to_add_if_true=review.missing_but_safe_to_add_if_true,
            missing_without_evidence=review.missing_without_evidence,
            provider_used=provider_used,
            requested_provider=str(runtime.requested_provider),
            analysis_mode=_analysis_mode(provider_used, fallback_used),
            fallback_used=fallback_used,
            ai_insights=ai_insights,
            warnings=warnings,
        ),
        warnings,
    )


def tailor_resume(request: ResumeTailorRequest) -> tuple[ResumeTailorResponse, list[str]]:
    """Build safe, evidence-backed tailoring suggestions."""
    runtime = get_ai_runtime("tailor")
    profile_context_text = _profile_context_text()
    evidence_text = request.evidence_text
    profile_context_applied = bool(profile_context_text) and (
        runtime.provider_name == "local" or runtime.allow_memory_context
    )
    if profile_context_applied:
        evidence_text = _append_profile_context(evidence_text, profile_context_text)
    tailor = build_safe_tailor_output(
        target_role=request.target_role,
        target_company=request.target_company,
        job_text=request.job_text,
        evidence_text=evidence_text,
        match_analysis=request.match_analysis,
    )
    warnings = [*tailor.warnings, *runtime.warnings]
    if profile_context_applied:
        warnings.append("Contexto do Perfil Profissional aplicado ao ajuste.")
    elif profile_context_text and runtime.provider_name != "local":
        warnings.append("Contexto do perfil nao foi enviado ao provider externo.")
    provider_used = runtime.provider_name
    fallback_used = runtime.fallback_used
    ai_suggestions: list[str] = []

    if runtime.use_ai and runtime.provider_name != "local":
        try:
            spec = default_prompt_registry().get("resume_tailor_v1")
            output = runtime.provider.generate_structured(
                spec,
                {
                    "target_role": request.target_role,
                    "target_company": request.target_company or "",
                    "job_text": request.job_text,
                    "evidence_text": evidence_text,
                    "deterministic_tailor": tailor.model_dump(mode="json"),
                    "language": "pt-BR",
                },
            )
            ai_tailor = ResumeTailorAiOutput.model_validate(output)
            ai_suggestions = _unique(
                [
                    *ai_tailor.suggested_bullets,
                    *ai_tailor.conditional_suggestions,
                    *ai_tailor.safe_keywords,
                ]
            )[:10]
            warnings.extend(ai_tailor.warnings)
        except Exception:
            provider_used = "local"
            fallback_used = True
            warnings.append("Gemini falhou no Ajuste de Curriculo; mantive sugestoes locais.")

    return (
        ResumeTailorResponse(
            tailor=tailor,
            safe_to_export=tailor.is_safe_to_export(),
            provider_used=provider_used,
            requested_provider=str(runtime.requested_provider),
            analysis_mode=_analysis_mode(provider_used, fallback_used),
            fallback_used=fallback_used,
            ai_suggestions=ai_suggestions,
        ),
        warnings,
    )


def analyze_github_repo(
    request: GitHubRepoAnalyzeRequest,
) -> tuple[GitHubRepoAnalyzeResponse, list[str]]:
    """Analyze a public GitHub repository through the existing analyzer."""
    runtime = get_ai_runtime("github")
    try:
        report = analyze_github_repository(
            request.repo_url,
            provider=runtime.provider if runtime.provider_name != "local" else None,
            analysis_input=request.to_analysis_input(),
            fallback_payload=request.fallback_payload,
        )
    except GitHubAnalyzerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    provider_used = report.provider_used
    fallback_used = report.fallback_used or (
        runtime.provider_name != "local" and not provider_used.startswith("gemini")
    )
    warnings = [*runtime.warnings]
    if report.fallback_used:
        warnings.append("Analise GitHub usou fallback local.")
    if fallback_used and runtime.provider_name != "local" and not report.fallback_used:
        warnings.append("Gemini nao retornou analise GitHub estruturada; usei analise local.")
    return (
        GitHubRepoAnalyzeResponse(
            report=report,
            provider_used=provider_used,
            requested_provider=str(runtime.requested_provider),
            analysis_mode=_analysis_mode(provider_used, fallback_used),
            fallback_used=fallback_used,
        ),
        warnings,
    )


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


def _append_profile_context(base_text: str, context_text: str) -> str:
    """Append profile context as explicit evidence, never invented facts."""
    if not context_text:
        return base_text
    return "\n\n".join(
        part
        for part in [
            base_text,
            "Evidencias do Perfil Profissional Universal local:",
            context_text,
            "Use apenas evidencias confirmadas; itens de baixa confianca ficam a confirmar.",
        ]
        if part
    )


def _profile_context_text() -> str:
    """Build a compact local profile evidence summary."""
    try:
        context = ProfileContextOrchestrator().build_context(purpose="analysis")
    except Exception:
        return ""
    sections: list[str] = []
    for label, items in [
        ("Formacao", context.education),
        ("Experiencias", context.experiences),
        ("Academico", context.academic_experiences),
        ("Projetos/portfolio", context.projects),
        ("Certificacoes/registros", context.certifications_and_registries),
        ("Competencias", context.skills),
        ("Idiomas", context.languages),
    ]:
        if not items:
            continue
        values = [
            f"{item.title} ({item.confidence}; {'confirmado' if item.confirmed_by_user else 'a confirmar'})"
            for item in items[:8]
        ]
        sections.append(f"{label}: {', '.join(values)}")
    if context.career_goals:
        sections.append(f"Objetivos: {', '.join(context.career_goals[:8])}")
    if context.constraints:
        sections.append(f"Restricoes: {', '.join(context.constraints[:8])}")
    return "\n".join(sections)


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


def _analysis_mode(provider_used: str, fallback_used: bool) -> Literal["local", "ai", "fallback"]:
    if fallback_used:
        return "fallback"
    return "local" if provider_used.startswith("local") else "ai"


def _safe_provider_warning(context: str, warning: str) -> str:
    if "Gemini" in warning:
        return f"{context}: Gemini indisponivel; usei fallback local."
    return f"{context}: provider opcional indisponivel; usei fallback local."
