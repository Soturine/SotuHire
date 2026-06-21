"""Structured job extraction with AI validation and local fallback."""

from __future__ import annotations

from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from modules.ai.json_guard import JsonGuardResult, collect_low_confidence_fields, validate_ai_json
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.prompt_registry import PromptRegistry
from modules.ai.schemas.common import ConfidenceSummary, CredentialSignal, StrictSchema
from modules.ai.schemas.job_extraction import (
    JobDomainClassification,
    JobExtractionOutput,
    JobIdentity,
    JobRequirement,
    JobSeniority,
    RedFlag,
    RequirementCategory,
    RequirementCriticality,
    RequirementImportance,
    SalaryInfo,
)
from modules.ai.structured_analysis import get_provider
from modules.core.text_utils import normalize_text
from modules.domain_intelligence.domain_classifier import classify_domain
from modules.domain_intelligence.requirement_types import classify_requirement
from modules.parsers.job_description_parser import parse_job_description
from modules.schemas.job_posting import JobPostingSchema

JobWorkModel = Literal["remote", "hybrid", "onsite", "field", "unknown"]
JobContractType = Literal[
    "clt",
    "pj",
    "internship",
    "temporary",
    "freelance",
    "trainee",
    "apprentice",
    "public_sector",
    "unknown",
]
JobSeniorityLevel = Literal[
    "intern",
    "apprentice",
    "assistant",
    "junior",
    "mid",
    "senior",
    "specialist",
    "coordinator",
    "manager",
    "director",
    "unknown",
]


class StructuredJobExtractionResult(StrictSchema):
    """Job extraction output plus provider and fallback metadata."""

    output: JobExtractionOutput
    local_job: JobPostingSchema
    provider: str
    requested_provider: str
    fallback_used: bool = False
    warning: str = ""
    low_confidence_fields: list[str] = Field(default_factory=list)


def extract_structured_job(
    job_text: str,
    *,
    source: dict[str, object] | None = None,
    candidate_context: dict[str, object] | None = None,
    provider: Any | None = None,
    registry: PromptRegistry | None = None,
) -> StructuredJobExtractionResult:
    """Extract structured multi-domain job facts with local fallback."""
    local_job = parse_job_description(job_text)
    selected = provider or get_provider()
    requested_provider = getattr(selected, "name", "unknown")
    prompt_registry = registry or default_prompt_registry()
    try:
        spec = prompt_registry.get("job_extraction_multi_domain_v1")
        payload = {
            "job_text": job_text,
            "source": source or {},
            "candidate_context": candidate_context or {},
            "local_job": local_job.model_dump(mode="json"),
            "language": "pt-BR",
        }
        result = _coerce_job_output(selected.generate_structured(spec, payload))
        output = _mark_job_disagreements(result.data, local_job)
        low_confidence = _merge_fields(
            result.low_confidence_fields,
            output.extraction_confidence.low_confidence_fields,
        )
        return StructuredJobExtractionResult(
            output=output,
            local_job=local_job,
            provider=requested_provider,
            requested_provider=requested_provider,
            low_confidence_fields=low_confidence,
        )
    except Exception as exc:
        fallback = _job_output_from_local(local_job, source or {})
        low_confidence = collect_low_confidence_fields(fallback.model_dump(mode="json"))
        return StructuredJobExtractionResult(
            output=fallback,
            local_job=local_job,
            provider="local",
            requested_provider=requested_provider,
            fallback_used=True,
            warning=f"Structured job extraction unavailable; local parser used. Reason: {exc}",
            low_confidence_fields=low_confidence,
        )


def _coerce_job_output(payload: Any) -> JsonGuardResult[JobExtractionOutput]:
    if isinstance(payload, JobExtractionOutput):
        return JsonGuardResult(
            data=payload,
            low_confidence_fields=collect_low_confidence_fields(payload.model_dump(mode="json")),
        )
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return validate_ai_json(payload, JobExtractionOutput)


def _job_output_from_local(
    job: JobPostingSchema,
    source: dict[str, object],
) -> JobExtractionOutput:
    domain_output = classify_domain(job.raw_text, text_type="job", known_context=source)
    primary = domain_output.primary_domain
    requirements = [
        *[_requirement_from_text(skill, "required", job.raw_text) for skill in job.required_skills],
        *[_requirement_from_text(skill, "preferred", job.raw_text) for skill in job.desired_skills],
    ]
    for alias in domain_output.aliases_detected:
        if alias.normalized_name not in {item.normalized_name for item in requirements}:
            requirements.append(
                _requirement_from_text(
                    alias.normalized_name,
                    "required" if alias.category == "professional_license" else "unclear",
                    job.raw_text,
                )
            )
    professional_licenses = [
        CredentialSignal(
            name=signal.credential,
            type="professional_license",
            status="unknown",
            evidence=[signal.evidence],
            confidence=signal.confidence,
        )
        for signal in domain_output.regulated_profession_signals
    ]
    missing_info = job.risk_flags
    confidence = 0.62 if missing_info else 0.78
    return JobExtractionOutput(
        job_identity=JobIdentity(
            title=job.title,
            company=job.company,
            source=str(source.get("platform") or source.get("type") or ""),
            url=str(source.get("url") or ""),
            location=job.location,
            work_model=_work_model(job.modality),
            contract_type=_contract_type(job.contract),
            salary=SalaryInfo(
                raw=_salary_raw(job),
                minimum=job.salary_min,
                maximum=job.salary_max,
                confidence=0.75 if job.salary_min is not None else 0.35,
            ),
            confidence=0.8 if job.title else 0.5,
        ),
        domain_classification=JobDomainClassification(
            primary_domain=primary.domain,
            secondary_domains=[domain.domain for domain in domain_output.secondary_domains],
            is_tech_job=primary.domain in {"software_engineering", "cybersecurity", "data", "qa"},
            is_regulated_profession=bool(professional_licenses),
            confidence=primary.confidence,
            evidence=primary.evidence,
        ),
        domains=[primary, *domain_output.secondary_domains],
        seniority=_job_seniority(job.seniority),
        requirements=requirements,
        responsibilities=_responsibilities_from_text(job.raw_text),
        tools=[item for item in requirements if item.category == "tool"],
        softwares=[item for item in requirements if item.category == "software"],
        equipment=[item for item in requirements if item.category == "equipment"],
        professional_licenses=professional_licenses,
        education_requirements=[item for item in requirements if item.category == "education"],
        benefits=job.benefits,
        red_flags=[
            RedFlag(type="missing_information", description=flag) for flag in job.risk_flags
        ],
        keywords_for_ats=job.ats_keywords,
        missing_job_information=missing_info,
        extraction_confidence=ConfidenceSummary(
            overall=confidence,
            low_confidence_fields=missing_info,
            needs_user_review=bool(missing_info) or confidence < 0.7,
            reason="Local heuristic fallback." if missing_info else "Local parser extraction.",
        ),
    )


def _mark_job_disagreements(
    output: JobExtractionOutput,
    local_job: JobPostingSchema,
) -> JobExtractionOutput:
    review_fields = set(output.extraction_confidence.low_confidence_fields)
    identity = output.job_identity
    comparisons = [
        ("job_identity.title", local_job.title, identity.title),
        ("job_identity.company", local_job.company, identity.company),
        ("job_identity.location", local_job.location, identity.location),
    ]
    for field, local_value, ai_value in comparisons:
        if local_value and ai_value and normalize_text(local_value) != normalize_text(ai_value):
            review_fields.add(field)
    confidence = output.extraction_confidence.model_copy(
        update={
            "low_confidence_fields": sorted(review_fields),
            "needs_user_review": output.extraction_confidence.needs_user_review
            or bool(review_fields),
        }
    )
    return output.model_copy(update={"extraction_confidence": confidence})


def _requirement_from_text(
    text: str,
    importance: str,
    evidence_text: str,
) -> JobRequirement:
    classification = classify_requirement(text)
    category = (
        classification.category
        if classification.category
        in {
            "education",
            "hard_skill",
            "soft_skill",
            "tool",
            "software",
            "equipment",
            "certification",
            "professional_license",
            "language",
            "experience",
            "methodology",
            "regulation",
            "responsibility",
            "availability",
            "location",
            "portfolio",
            "other",
        }
        else "other"
    )
    requirement_importance = (
        importance if importance in {"required", "preferred", "optional"} else "unclear"
    )
    criticality = (
        classification.criticality
        if classification.criticality in {"low", "medium", "high", "knockout"}
        else "medium"
    )
    return JobRequirement(
        text=text,
        normalized_name=classification.normalized_name or text,
        category=cast(RequirementCategory, category),
        importance=cast(RequirementImportance, requirement_importance),
        criticality=cast(RequirementCriticality, criticality),
        domain=classification.domain,
        evidence=text if normalize_text(text) in normalize_text(evidence_text) else "",
        confidence=max(classification.confidence, 0.65),
    )


def _work_model(modality: str) -> JobWorkModel:
    return cast(
        JobWorkModel,
        {"remote": "remote", "hybrid": "hybrid", "onsite": "onsite"}.get(modality, "unknown"),
    )


def _contract_type(contract: str) -> JobContractType:
    normalized = normalize_text(contract)
    return cast(
        JobContractType,
        {
            "clt": "clt",
            "pj": "pj",
            "estagio": "internship",
            "temporario": "temporary",
            "freelance": "freelance",
            "trainee": "trainee",
        }.get(normalized, "unknown"),
    )


def _job_seniority(seniority: str) -> JobSeniority:
    normalized = normalize_text(seniority)
    level = {
        "estagio": "intern",
        "jovem aprendiz": "apprentice",
        "assistente": "assistant",
        "junior": "junior",
        "pleno": "mid",
        "senior": "senior",
        "especialista": "specialist",
    }.get(normalized, "unknown")
    return JobSeniority(
        level=cast(JobSeniorityLevel, level),
        evidence=[seniority] if seniority else [],
        confidence=0.72,
    )


def _salary_raw(job: JobPostingSchema) -> str:
    if job.salary_min is None:
        return ""
    if job.salary_max and job.salary_max != job.salary_min:
        return f"R$ {job.salary_min} - R$ {job.salary_max}"
    return f"R$ {job.salary_min}"


def _responsibilities_from_text(text: str) -> list[str]:
    lines = [line.strip(" -*") for line in text.splitlines() if line.strip()]
    return [
        line
        for line in lines
        if any(term in normalize_text(line) for term in ["responsavel", "atuar", "realizar"])
    ][:8]


def _merge_fields(*field_groups: list[str]) -> list[str]:
    return list(dict.fromkeys(field for group in field_groups for field in group))
