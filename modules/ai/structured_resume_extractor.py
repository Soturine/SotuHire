"""Structured resume extraction with AI validation and local fallback."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from modules.ai.json_guard import JsonGuardResult, collect_low_confidence_fields, validate_ai_json
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.prompt_registry import PromptRegistry
from modules.ai.schemas.common import (
    ConfidenceSummary,
    CredentialSignal,
    DomainSignal,
    LanguageSignal,
    StrictSchema,
)
from modules.ai.schemas.resume_extraction import (
    AtsObservations,
    CandidateIdentity,
    EducationEntry,
    ExperienceEntry,
    ExtractedSkill,
    ProfessionalSummary,
    ProjectEntry,
    ResumeExtractionOutput,
    SenioritySignal,
)
from modules.ai.structured_analysis import get_provider
from modules.core.text_utils import normalize_text
from modules.domain_intelligence.domain_classifier import classify_domain
from modules.domain_intelligence.requirement_types import classify_requirement
from modules.parsers.resume_parser import parse_resume_text
from modules.schemas.resume_profile import ResumeProfileSchema


class StructuredResumeExtractionResult(StrictSchema):
    """Resume extraction output plus provider and fallback metadata."""

    output: ResumeExtractionOutput
    local_profile: ResumeProfileSchema
    provider: str
    requested_provider: str
    fallback_used: bool = False
    warning: str = ""
    low_confidence_fields: list[str] = Field(default_factory=list)


def extract_structured_resume(
    resume_text: str,
    *,
    file_type: str = "text",
    candidate_preferences: dict[str, object] | None = None,
    existing_profile_memory: dict[str, object] | None = None,
    provider: Any | None = None,
    registry: PromptRegistry | None = None,
) -> StructuredResumeExtractionResult:
    """Extract structured resume facts with schema validation and local fallback."""
    local_profile = parse_resume_text(resume_text, source_type=file_type)
    selected = provider or get_provider()
    requested_provider = getattr(selected, "name", "unknown")
    prompt_registry = registry or default_prompt_registry()
    try:
        spec = prompt_registry.get("resume_extraction_v1")
        payload = {
            "resume_text": resume_text,
            "file_type": file_type,
            "candidate_preferences": candidate_preferences or {},
            "existing_profile_memory": existing_profile_memory or {},
            "local_profile": local_profile.model_dump(mode="json"),
            "language": "pt-BR",
        }
        result = _coerce_resume_output(selected.generate_structured(spec, payload))
        output = _mark_resume_disagreements(result.data, local_profile)
        low_confidence = _merge_fields(
            result.low_confidence_fields,
            output.extraction_confidence.low_confidence_fields,
        )
        return StructuredResumeExtractionResult(
            output=output,
            local_profile=local_profile,
            provider=requested_provider,
            requested_provider=requested_provider,
            low_confidence_fields=low_confidence,
        )
    except Exception as exc:
        fallback = _resume_output_from_local(local_profile)
        low_confidence = collect_low_confidence_fields(fallback.model_dump(mode="json"))
        return StructuredResumeExtractionResult(
            output=fallback,
            local_profile=local_profile,
            provider="local",
            requested_provider=requested_provider,
            fallback_used=True,
            warning=f"Structured resume extraction unavailable; local parser used. Reason: {exc}",
            low_confidence_fields=low_confidence,
        )


def _coerce_resume_output(payload: Any) -> JsonGuardResult[ResumeExtractionOutput]:
    if isinstance(payload, ResumeExtractionOutput):
        return JsonGuardResult(
            data=payload,
            low_confidence_fields=collect_low_confidence_fields(payload.model_dump(mode="json")),
        )
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return validate_ai_json(payload, ResumeExtractionOutput)


def _resume_output_from_local(profile: ResumeProfileSchema) -> ResumeExtractionOutput:
    domain_output = classify_domain(profile.raw_text, text_type="resume")
    missing_sections = _missing_resume_sections(profile)
    skills = [_skill_entry(skill, profile.raw_text) for skill in profile.skills]
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
    confidence = 0.62 if missing_sections else 0.76
    low_fields = [f"missing_sections.{section}" for section in missing_sections]
    return ResumeExtractionOutput(
        candidate_identity=CandidateIdentity(
            name=profile.name,
            email=profile.email,
            email_present=bool(profile.email),
            phone=profile.phone,
            phone_present=bool(profile.phone),
            location=profile.city,
            links=profile.links,
            confidence=0.82 if profile.name or profile.email else 0.55,
        ),
        professional_summary=ProfessionalSummary(
            summary_text=profile.summary,
            confidence=0.75 if profile.summary else 0.4,
        ),
        domains=[domain_output.primary_domain, *domain_output.secondary_domains],
        seniority=_detect_resume_seniority(profile.raw_text),
        education=[
            EducationEntry(course=item, evidence=[item], confidence=0.75)
            for item in profile.education
        ],
        experiences=[
            ExperienceEntry(
                title=item.splitlines()[0][:120],
                responsibilities=[item],
                evidence=[item],
                confidence=0.72,
            )
            for item in profile.experiences
        ],
        projects=[
            ProjectEntry(
                name=item.splitlines()[0][:120],
                description=item,
                evidence=[item],
                confidence=0.72,
            )
            for item in profile.projects
        ],
        skills=skills,
        tools=[skill for skill in skills if skill.category == "tool"],
        softwares=[skill for skill in skills if skill.category == "software"],
        equipment=[skill for skill in skills if skill.category == "equipment"],
        certifications=[
            CredentialSignal(
                name=item,
                type="certification",
                status="unknown",
                evidence=[item],
                confidence=0.68,
            )
            for item in profile.certifications
        ],
        professional_licenses=professional_licenses,
        languages=[
            LanguageSignal(language=item, evidence=[item], confidence=0.7)
            for item in profile.languages
        ],
        missing_sections=missing_sections,
        ats_observations=AtsObservations(
            missing_sections=missing_sections,
            keyword_risks=[] if profile.keywords else ["No relevant keywords detected."],
        ),
        extraction_confidence=ConfidenceSummary(
            overall=confidence,
            low_confidence_fields=low_fields,
            needs_user_review=bool(missing_sections) or confidence < 0.7,
            reason="Local heuristic fallback." if missing_sections else "Local parser extraction.",
        ),
    )


def _mark_resume_disagreements(
    output: ResumeExtractionOutput,
    local_profile: ResumeProfileSchema,
) -> ResumeExtractionOutput:
    review_fields = set(output.extraction_confidence.low_confidence_fields)
    identity = output.candidate_identity
    comparisons = [
        ("candidate_identity.name", local_profile.name, identity.name),
        ("candidate_identity.email", local_profile.email, identity.email),
        ("candidate_identity.phone", local_profile.phone, identity.phone),
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


def _skill_entry(skill: str, evidence_text: str) -> ExtractedSkill:
    classification = classify_requirement(skill)
    return ExtractedSkill(
        name=skill,
        normalized_name=classification.normalized_name or skill,
        category=classification.category
        if classification.category
        in {
            "hard_skill",
            "soft_skill",
            "tool",
            "software",
            "equipment",
            "methodology",
            "language",
            "certification",
            "professional_license",
            "regulation",
            "domain_knowledge",
            "other",
        }
        else "hard_skill",
        evidence=[skill] if normalize_text(skill) in normalize_text(evidence_text) else [],
        confidence=max(classification.confidence, 0.7),
    )


def _detect_resume_seniority(text: str) -> SenioritySignal:
    normalized = normalize_text(text)
    terms = [
        ("estagio", "intern"),
        ("jovem aprendiz", "apprentice"),
        ("assistente", "assistant"),
        ("junior", "junior"),
        ("pleno", "mid"),
        ("senior", "senior"),
        ("especialista", "specialist"),
        ("coordenador", "coordinator"),
        ("gerente", "manager"),
    ]
    for term, level in terms:
        if term in normalized:
            return SenioritySignal(
                estimated_level=level,
                reasoning=f"Detected seniority term: {term}.",
                evidence=[term],
                confidence=0.72,
            )
    return SenioritySignal(
        estimated_level="unknown",
        reasoning="No explicit seniority signal found.",
        confidence=0.35,
    )


def _missing_resume_sections(profile: ResumeProfileSchema) -> list[str]:
    checks = [
        ("contact", bool(profile.email or profile.phone)),
        ("education", bool(profile.education)),
        ("experience", bool(profile.experiences)),
        ("skills", bool(profile.skills)),
    ]
    return [section for section, present in checks if not present]


def _merge_fields(*field_groups: list[str]) -> list[str]:
    return list(dict.fromkeys(field for group in field_groups for field in group))
