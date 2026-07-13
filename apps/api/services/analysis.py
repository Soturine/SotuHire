"""Thin service layer over existing SotuHire domain modules."""

from __future__ import annotations

import os
from contextlib import suppress
from typing import Literal, TypedDict

from fastapi import HTTPException
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.schemas.analysis_insights import AtsAiReviewOutput, ResumeTailorAiOutput
from modules.ai.structured_analysis import analyze_structured
from modules.ai.structured_job_extractor import extract_structured_job
from modules.ai.structured_resume_extractor import extract_structured_resume
from modules.ats.match_keywords import review_keywords_with_match
from modules.context import (
    CareerContext,
    CareerContextEngine,
    CareerContextEvidence,
    CareerContextPurpose,
    context_brief,
    context_to_memory_evidence,
    format_context_for_prompt,
    profile_evidence_candidates_from_github_report,
)
from modules.core.entity_identity import content_fingerprint
from modules.core.text_utils import normalize_text
from modules.github_analyzer.analyzer_service import analyze_github_repository
from modules.github_analyzer.exceptions import GitHubAnalyzerError
from modules.parsers.job_description_parser import parse_job_description
from modules.parsers.resume_parser import parse_resume_text
from modules.resume_tailor.tailor_rules import build_safe_tailor_output
from modules.schemas.job_posting import JobPostingSchema
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.storage.ai_runs import AiRun, AiRunStore

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
from apps.api.services.ai_settings import AiRuntime, get_ai_runtime


class _TraceMetadataPayload(TypedDict):
    """Keyword payload shared by the typed analysis response models."""

    provider_requested: str
    requested_provider: str
    provider_used: str
    model_requested: str
    model_used: str
    prompt_id: str
    prompt_version: str
    analysis_mode: Literal["local", "ai", "fallback"]
    fallback_used: bool
    fallback_reason: str
    request_id: str
    source_refs: list[str]
    evidence_used: list[CareerContextEvidence]
    needs_user_review: bool


def extract_resume(request: ResumeExtractRequest) -> tuple[ResumeExtractResponse, list[str]]:
    """Parse a resume and return warnings separately for the API envelope."""
    runtime = get_ai_runtime("resume")
    warnings = list(runtime.warnings)
    low_confidence: list[str] = []
    provider_used = runtime.provider_name
    fallback_used = runtime.fallback_used

    if runtime.use_ai and runtime.provider_name != "local":
        result = extract_structured_resume(
            request.resume_text,
            file_type=request.source_type,
            provider=runtime.provider,
        )
        profile = result.local_profile
        provider_used = result.provider
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
            low_confidence_fields=low_confidence,
            **_trace_metadata(
                feature="resume",
                runtime=runtime,
                provider_used=provider_used,
                fallback_used=fallback_used,
                prompt_id="resume_extraction_v1",
                request_id=request.request_id,
                warnings=warnings,
            ),
        ),
        warnings,
    )


def extract_job(request: JobExtractRequest) -> tuple[JobExtractResponse, list[str]]:
    """Parse a job description and return warnings separately for the API envelope."""
    runtime = get_ai_runtime("job")
    warnings = list(runtime.warnings)
    low_confidence: list[str] = []
    provider_used = runtime.provider_name
    fallback_used = runtime.fallback_used

    if runtime.use_ai and runtime.provider_name != "local":
        result = extract_structured_job(
            request.job_text,
            source={"url": request.source_url} if request.source_url else {},
            provider=runtime.provider,
        )
        job = result.local_job
        provider_used = result.provider
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
            low_confidence_fields=low_confidence,
            **_trace_metadata(
                feature="job",
                runtime=runtime,
                provider_used=provider_used,
                fallback_used=fallback_used,
                prompt_id="job_extraction_multi_domain_v1",
                request_id=request.request_id,
                source_refs=[request.source_url],
                warnings=warnings,
            ),
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
    career_context = _build_career_context(
        CareerContextPurpose.MATCH,
        query=" ".join([resume_text, job_text]),
    )
    external_share = runtime.provider_name != "local" and runtime.allow_memory_context
    memory_evidence = context_to_memory_evidence(
        career_context,
        include_sensitive=not external_share,
    )
    result = analyze_structured(
        resume_text,
        job_text,
        preferences=request.preferences,
        job_details=(request.job.model_dump() if request.job else None),
        provider=runtime.provider,
        memory_evidence=memory_evidence,
        share_memory_with_provider=runtime.allow_memory_context,
    )
    warnings = [
        *runtime.warnings,
        *career_context.warnings,
        *([result.warning] if result.warning else []),
    ]
    if memory_evidence:
        warnings.append("Career Context Engine aplicado como evidencia local.")
    if memory_evidence and runtime.provider_name != "local" and not runtime.allow_memory_context:
        warnings.append("Contexto de carreira nao foi enviado ao provider externo.")
    if external_share and any(item.sensitive for item in career_context.evidence):
        warnings.append("Evidencias sensiveis foram omitidas do contexto externo.")
    return (
        MatchAnalyzeResponse(
            analysis=result.analysis,
            local_first=result.provider == "local",
            model=result.model,
            memory_shared_with_provider=result.memory_shared_with_provider,
            context_summary=context_brief(career_context),
            context_evidence_count=len(memory_evidence),
            context_warnings=career_context.warnings,
            **_trace_metadata(
                feature="match",
                runtime=runtime,
                provider_used=result.provider,
                fallback_used=result.fallback_used,
                prompt_id="match_analysis_evidence_based_v1",
                request_id=request.request_id,
                context=career_context,
                warnings=warnings,
                model_used=result.model if result.provider != "local" else "local",
            ),
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
    career_context = _build_career_context(
        CareerContextPurpose.ATS,
        query=" ".join([request.job_text, " ".join(keywords)]),
    )
    context_keywords = _context_keywords_for_ats(career_context, keywords)
    keywords_without_context = [keyword for keyword in keywords if keyword not in context_keywords]
    profile_or_rag_terms = _profile_or_rag_terms_for_ats(career_context)
    if context_keywords:
        warnings.append("ATS consultou evidencias do Career Context Engine.")
    provider_used = runtime.provider_name
    fallback_used = runtime.fallback_used
    ai_insights: list[str] = [
        f"Evidencia local encontrada para: {keyword}" for keyword in context_keywords[:8]
    ]

    if runtime.use_ai and runtime.provider_name != "local":
        try:
            spec = default_prompt_registry().get("ats_analysis_v1")
            external_context = (
                format_context_for_prompt(
                    career_context,
                    include_sensitive=False,
                    confirmed_only=True,
                )
                if runtime.allow_memory_context
                else ""
            )
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
                    "career_context": external_context,
                    "language": "pt-BR",
                },
            )
            ai_review = AtsAiReviewOutput.model_validate(output)
            ai_insights = _unique(
                [
                    *ai_insights,
                    *ai_review.keyword_observations,
                    *ai_review.safe_to_add_if_true,
                ]
            )[:8]
            warnings.extend(ai_review.warnings)
        except Exception:
            provider_used = "local"
            fallback_used = True
            warnings.append("Provider de IA falhou na análise ATS; mantive a revisão local.")

    return (
        AtsAnalyzeResponse(
            ats_score=analysis.ats_score,
            present=review.present,
            missing_but_safe_to_add_if_true=review.missing_but_safe_to_add_if_true,
            missing_without_evidence=review.missing_without_evidence,
            ai_insights=ai_insights,
            warnings=warnings,
            context_summary=context_brief(career_context),
            context_evidence_keywords=context_keywords,
            safe_keywords_from_context=context_keywords,
            keywords_without_context_evidence=keywords_without_context,
            profile_or_rag_terms=profile_or_rag_terms,
            unevidenced_profile_claims=[
                keyword
                for keyword in review.missing_but_safe_to_add_if_true
                if keyword not in context_keywords
            ],
            **_trace_metadata(
                feature="ats",
                runtime=runtime,
                provider_used=provider_used,
                fallback_used=fallback_used,
                prompt_id="ats_analysis_v1",
                request_id=request.request_id,
                context=career_context,
                warnings=warnings,
            ),
        ),
        warnings,
    )


def tailor_resume(request: ResumeTailorRequest) -> tuple[ResumeTailorResponse, list[str]]:
    """Build safe, evidence-backed tailoring suggestions."""
    runtime = get_ai_runtime("tailor")
    career_context = _build_career_context(
        CareerContextPurpose.TAILOR,
        query=" ".join([request.target_role, request.job_text, request.evidence_text]),
    )
    context_text = format_context_for_prompt(
        career_context,
        include_sensitive=False,
        confirmed_only=True,
    )
    local_evidence_text = _append_profile_context(request.evidence_text, context_text)
    provider_evidence_text = (
        local_evidence_text
        if runtime.provider_name == "local" or runtime.allow_memory_context
        else request.evidence_text
    )
    tailor = build_safe_tailor_output(
        target_role=request.target_role,
        target_company=request.target_company,
        job_text=request.job_text,
        evidence_text=local_evidence_text,
        match_analysis=request.match_analysis,
    )
    warnings = [*tailor.warnings, *runtime.warnings, *career_context.warnings]
    if context_text:
        warnings.append("Career Context Engine aplicado ao ajuste local.")
    if context_text and runtime.provider_name != "local" and not runtime.allow_memory_context:
        warnings.append("Contexto de carreira nao foi enviado ao provider externo.")
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
                    "evidence_text": provider_evidence_text,
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
            warnings.append(
                "Provider de IA falhou no ajuste de currículo; mantive sugestões locais."
            )

    return (
        ResumeTailorResponse(
            tailor=tailor,
            safe_to_export=tailor.is_safe_to_export(),
            ai_suggestions=ai_suggestions,
            context_summary=context_brief(career_context),
            context_evidence_count=len(career_context.evidence),
            **_trace_metadata(
                feature="tailor",
                runtime=runtime,
                provider_used=provider_used,
                fallback_used=fallback_used,
                prompt_id="resume_tailor_v1",
                request_id=request.request_id,
                context=career_context,
                warnings=warnings,
            ),
        ),
        warnings,
    )


def analyze_github_repo(
    request: GitHubRepoAnalyzeRequest,
) -> tuple[GitHubRepoAnalyzeResponse, list[str]]:
    """Analyze a public GitHub repository through the existing analyzer."""
    runtime = get_ai_runtime("github")
    career_context = _build_career_context(
        CareerContextPurpose.GITHUB,
        query=" ".join([request.repo_url, request.target_role]),
    )
    analysis_input = request.to_analysis_input()
    if not analysis_input.candidate_profile:
        safe_context = {
            "summary": context_brief(career_context),
            "goals": career_context.goals[:8],
            "domains": career_context.domains[:8],
            "evidence": [
                item.model_dump(mode="json")
                for item in career_context.evidence
                if not item.sensitive and item.confirmed_by_user
            ][:8],
        }
        if runtime.provider_name == "local" or runtime.allow_memory_context:
            analysis_input = analysis_input.model_copy(update={"candidate_profile": safe_context})
    try:
        report = analyze_github_repository(
            request.repo_url,
            provider=runtime.provider if runtime.provider_name != "local" else None,
            analysis_input=analysis_input,
            fallback_payload=request.fallback_payload,
        )
    except GitHubAnalyzerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    provider_used = report.provider_used
    fallback_used = report.fallback_used or (
        runtime.provider_name != "local" and not provider_used.startswith(runtime.provider_name)
    )
    warnings = [*runtime.warnings, *career_context.warnings]
    if report.fallback_used:
        warnings.append("Analise GitHub usou fallback local.")
    if fallback_used and runtime.provider_name != "local" and not report.fallback_used:
        warnings.append("Provider não retornou análise GitHub estruturada; usei análise local.")
    return (
        GitHubRepoAnalyzeResponse(
            report=report,
            profile_evidence_candidates=profile_evidence_candidates_from_github_report(report),
            **_trace_metadata(
                feature="github",
                runtime=runtime,
                provider_used=provider_used,
                fallback_used=fallback_used,
                prompt_id="github_repo_analysis_v2",
                request_id=request.request_id,
                context=career_context,
                source_refs=[request.repo_url],
                warnings=warnings,
            ),
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


def _build_career_context(purpose: CareerContextPurpose, *, query: str = "") -> CareerContext:
    return CareerContextEngine().build(purpose, query=query, max_evidence=12)


def _context_keywords_for_ats(
    context: CareerContext,
    keywords: list[str],
) -> list[str]:
    supported: list[str] = []
    evidence_text = normalize_text(
        " ".join(
            [
                context.profile_summary,
                *context.goals,
                *context.domains,
                *[
                    f"{item.title} {item.content}"
                    for item in context.evidence
                    if not item.sensitive and item.confirmed_by_user
                ],
            ]
        )
    )
    for keyword in keywords:
        normalized = normalize_text(keyword)
        if normalized and normalized in evidence_text:
            supported.append(keyword)
    return _unique(supported)


def _profile_or_rag_terms_for_ats(context: CareerContext) -> list[str]:
    terms: list[str] = []
    for item in context.evidence:
        if item.sensitive:
            continue
        terms.append(item.title)
        terms.append(item.kind)
        terms.append(item.source)
    terms.extend([*context.goals, *context.domains, *context.contract_types])
    return _unique([term for term in terms if 2 <= len(str(term)) <= 80])[:40]


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


def _analysis_mode(provider_used: str, fallback_used: bool) -> Literal["local", "ai", "fallback"]:
    if fallback_used:
        return "fallback"
    return "local" if provider_used.startswith("local") else "ai"


def _safe_provider_warning(context: str, warning: str) -> str:
    _ = warning
    return f"{context}: provider opcional indisponível; usei fallback local."


def _trace_metadata(
    *,
    feature: str,
    runtime: AiRuntime,
    provider_used: str,
    fallback_used: bool,
    prompt_id: str,
    request_id: str,
    context: CareerContext | None = None,
    source_refs: list[str] | None = None,
    warnings: list[str] | None = None,
    model_used: str = "",
) -> _TraceMetadataPayload:
    """Build one complete trace without exposing provider secrets or sensitive evidence."""
    spec = default_prompt_registry().get(prompt_id)
    evidence = [item for item in (context.evidence if context else []) if not item.sensitive]
    refs = _unique(
        [
            *(source_refs or []),
            *[item.source_ref for item in evidence if item.source_ref],
        ]
    )
    fallback_reason = ""
    if fallback_used:
        fallback_reason = next(
            (
                warning
                for warning in warnings or []
                if any(
                    term in normalize_text(warning) for term in ("falh", "indispon", "sem chave")
                )
            ),
            "Provider solicitado indisponivel; analise local utilizada.",
        )
    requested = str(runtime.requested_provider)
    effective_model = model_used or (runtime.model if provider_used != "local" else "local")
    trace: _TraceMetadataPayload = {
        "provider_requested": requested,
        "requested_provider": requested,
        "provider_used": provider_used,
        "model_requested": runtime.model_requested,
        "model_used": effective_model,
        "prompt_id": spec.prompt_id,
        "prompt_version": spec.version,
        "analysis_mode": _analysis_mode(provider_used, fallback_used),
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "request_id": request_id,
        "source_refs": refs,
        "evidence_used": evidence,
        "needs_user_review": True,
    }
    if not (os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("SOTUHIRE_DATA_DIR")):
        with suppress(OSError, ValueError):
            AiRunStore().save(
                AiRun(
                    feature=feature,
                    provider_requested=requested,
                    provider_used=provider_used,
                    model_requested=runtime.model_requested,
                    model_used=effective_model,
                    prompt_id=spec.prompt_id,
                    prompt_version=spec.version,
                    analysis_mode=trace["analysis_mode"],
                    fallback_used=fallback_used,
                    fallback_reason=fallback_reason,
                    schema_valid=True,
                    input_hash=content_fingerprint(
                        request_id,
                        " ".join(refs),
                        context.purpose.value if context else prompt_id,
                    ),
                    context_sources=_unique([item.source for item in evidence]),
                    source_refs=refs,
                    evidence_used=[item.model_dump(mode="json") for item in evidence],
                    warnings=list(warnings or []),
                    needs_user_review=True,
                )
            )
    return trace
