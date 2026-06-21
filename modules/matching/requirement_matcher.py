"""Requirement normalization and matching for Match Engine 2."""

from __future__ import annotations

import re
from dataclasses import dataclass

from modules.ai.schemas.job_extraction import JobExtractionOutput, JobRequirement
from modules.core.text_utils import normalize_text
from modules.domain_intelligence.aliases import AliasEntry, normalize_alias
from modules.matching.models import (
    CandidateEvidence,
    GapSeverity,
    MatchRequirement,
    RequirementCategory,
    RequirementCriticality,
    RequirementImportance,
    RequirementMatch,
)


@dataclass(frozen=True)
class ProfessionalCredential:
    """Known professional license or registration signal."""

    code: str
    label: str
    category: RequirementCategory
    domain: str


PROFESSIONAL_CREDENTIALS: dict[str, ProfessionalCredential] = {
    "crm": ProfessionalCredential(
        "CRM", "Conselho Regional de Medicina", "professional_license", "healthcare"
    ),
    "cro": ProfessionalCredential(
        "CRO", "Conselho Regional de Odontologia", "professional_license", "healthcare"
    ),
    "crf": ProfessionalCredential(
        "CRF", "Conselho Regional de Farmacia", "professional_license", "healthcare"
    ),
    "coren": ProfessionalCredential(
        "COREN", "Conselho Regional de Enfermagem", "professional_license", "nursing"
    ),
    "crefito": ProfessionalCredential(
        "CREFITO",
        "Conselho Regional de Fisioterapia e Terapia Ocupacional",
        "professional_license",
        "healthcare",
    ),
    "crn": ProfessionalCredential(
        "CRN", "Conselho Regional de Nutricao", "professional_license", "healthcare"
    ),
    "crmv": ProfessionalCredential(
        "CRMV", "Conselho Regional de Medicina Veterinaria", "professional_license", "healthcare"
    ),
    "crp": ProfessionalCredential(
        "CRP", "Conselho Regional de Psicologia", "professional_license", "psychology"
    ),
    "cref": ProfessionalCredential(
        "CREF", "Conselho Regional de Educacao Fisica", "professional_license", "education"
    ),
    "crtr": ProfessionalCredential(
        "CRTR", "Conselho Regional de Tecnicos em Radiologia", "professional_license", "healthcare"
    ),
    "crea": ProfessionalCredential(
        "CREA", "Conselho Regional de Engenharia e Agronomia", "professional_license", "engineering"
    ),
    "cau": ProfessionalCredential(
        "CAU", "Conselho de Arquitetura e Urbanismo", "professional_license", "architecture"
    ),
    "cft": ProfessionalCredential(
        "CFT",
        "Conselho Federal dos Tecnicos Industriais",
        "professional_license",
        "technical_course",
    ),
    "crt": ProfessionalCredential(
        "CRT",
        "Conselho Regional dos Tecnicos Industriais",
        "professional_license",
        "technical_course",
    ),
    "crq": ProfessionalCredential(
        "CRQ", "Conselho Regional de Quimica", "professional_license", "industrial"
    ),
    "oab": ProfessionalCredential(
        "OAB", "Ordem dos Advogados do Brasil", "professional_license", "business"
    ),
    "crc": ProfessionalCredential(
        "CRC", "Conselho Regional de Contabilidade", "professional_license", "finance"
    ),
    "cra": ProfessionalCredential(
        "CRA", "Conselho Regional de Administracao", "professional_license", "business"
    ),
    "corecon": ProfessionalCredential(
        "CORECON", "Conselho Regional de Economia", "professional_license", "finance"
    ),
    "crb": ProfessionalCredential(
        "CRB", "Conselho Regional de Biblioteconomia", "professional_license", "education"
    ),
    "cress": ProfessionalCredential(
        "CRESS", "Conselho Regional de Servico Social", "professional_license", "social_services"
    ),
    "conrerp": ProfessionalCredential(
        "CONRERP", "Conselho Regional de Relacoes Publicas", "professional_license", "communication"
    ),
    "creci": ProfessionalCredential(
        "CRECI", "Conselho Regional de Corretores de Imoveis", "professional_license", "business"
    ),
    "crbio": ProfessionalCredential(
        "CRBio", "Conselho Regional de Biologia", "professional_license", "healthcare"
    ),
    "mte": ProfessionalCredential(
        "MTE", "Registro profissional MTE", "professional_registration", "general"
    ),
    "drt": ProfessionalCredential(
        "DRT", "Registro profissional DRT", "professional_registration", "general"
    ),
}

REQUIRED_TERMS = {
    "obrigatorio",
    "obrigatoria",
    "necessario",
    "necessaria",
    "exige",
    "requer",
    "mandatorio",
}
PREFERRED_TERMS = {"desejavel", "diferencial", "preferencial", "plus", "seria um diferencial"}
OPTIONAL_TERMS = {"opcional", "nice to have"}


def classify_professional_credential(term: str) -> ProfessionalCredential | None:
    """Return a known professional credential by acronym."""
    return PROFESSIONAL_CREDENTIALS.get(normalize_text(term))


def detect_professional_credentials(text: str) -> list[ProfessionalCredential]:
    """Detect professional license/registration acronyms in text."""
    normalized = normalize_text(text)
    detected: list[ProfessionalCredential] = []
    for key, credential in PROFESSIONAL_CREDENTIALS.items():
        if re.search(rf"(?<!\w){re.escape(key)}(?!\w)", normalized):
            detected.append(credential)
    return detected


def normalize_requirement(
    requirement_text: str,
    *,
    category: RequirementCategory | str = "other",
    importance: RequirementImportance | str = "unclear",
    criticality: str = "medium",
    domain: str = "",
    evidence: str = "",
    confidence: float = 0.7,
) -> MatchRequirement:
    """Normalize one job requirement with aliases and professional credential rules."""
    text = requirement_text.strip()
    alias = normalize_alias(text)
    credential = _first_credential(text)
    normalized_name = credential.code if credential else _alias_name(alias, text)
    inferred_importance = _infer_importance(text, str(importance))
    inferred_category = _infer_category(text, str(category), alias, credential)
    inferred_criticality = _infer_criticality(str(criticality), inferred_importance, credential)
    return MatchRequirement(
        requirement_text=text,
        normalized_name=normalized_name,
        category=inferred_category,
        importance=inferred_importance,
        criticality=inferred_criticality,
        domain=credential.domain if credential else domain or (alias.domain if alias else ""),
        evidence=evidence or text,
        confidence=confidence,
    )


def requirements_from_job_extraction(job: JobExtractionOutput) -> list[MatchRequirement]:
    """Build Match Engine requirements from v0.10 structured job extraction."""
    requirements: list[MatchRequirement] = []
    for item in [
        *job.requirements,
        *job.tools,
        *job.softwares,
        *job.equipment,
        *job.education_requirements,
    ]:
        requirements.append(_from_job_requirement(item))
    for credential in [*job.certifications, *job.professional_licenses]:
        requirements.append(
            normalize_requirement(
                credential.name,
                category=credential.type if credential.type != "course" else "certification",
                importance="required",
                criticality="knockout" if credential.type == "professional_license" else "high",
                evidence="; ".join(credential.evidence),
                confidence=credential.confidence,
            )
        )
    return _dedupe_requirements(requirements)


def match_requirements(
    requirements: list[MatchRequirement],
    evidence: list[CandidateEvidence],
) -> list[RequirementMatch]:
    """Match each requirement against candidate evidence."""
    return [match_requirement(requirement, evidence) for requirement in requirements]


def match_requirement(
    requirement: MatchRequirement,
    evidence: list[CandidateEvidence],
) -> RequirementMatch:
    """Compare one requirement against normalized candidate evidence."""
    matching = [_evidence for _evidence in evidence if _matches(requirement, _evidence)]
    if matching:
        confidence = min(0.98, max(item.confidence for item in matching) + 0.05)
        return RequirementMatch(
            requirement=requirement,
            match_status="matched",
            candidate_evidence=matching,
            evidence_source=matching[0].evidence_source,
            confidence=confidence,
            gap_severity="none",
            safe_action="Manter essa evidência visível e conectada à vaga.",
        )

    partial = [_evidence for _evidence in evidence if _partial_matches(requirement, _evidence)]
    if partial:
        return RequirementMatch(
            requirement=requirement,
            match_status="partial",
            candidate_evidence=partial,
            evidence_source=partial[0].evidence_source,
            confidence=max(0.35, min(0.75, max(item.confidence for item in partial))),
            gap_severity="medium" if requirement.importance == "required" else "low",
            safe_action="Descrever a experiência relacionada sem afirmar domínio direto sem evidência.",
        )

    severity = _missing_gap_severity(requirement)
    return RequirementMatch(
        requirement=requirement,
        match_status="missing",
        candidate_evidence=[],
        evidence_source="none",
        confidence=max(0.2, requirement.confidence),
        gap_severity=severity,
        safe_action=_missing_safe_action(requirement, severity),
    )


def evidence_from_text(
    text: str,
    *,
    source: str = "resume",
    category: RequirementCategory = "other",
    confidence: float = 0.65,
) -> list[CandidateEvidence]:
    """Create candidate evidence from plain text and known aliases."""
    evidence: list[CandidateEvidence] = []
    for credential in detect_professional_credentials(text):
        evidence.append(
            CandidateEvidence(
                skill=credential.code,
                normalized_name=credential.code,
                category=credential.category,
                evidence_source=source,  # type: ignore[arg-type]
                evidence_text=credential.label,
                strength="strong",
                confidence=0.9,
            )
        )
    alias = normalize_alias(text)
    if alias:
        evidence.append(
            CandidateEvidence(
                skill=alias.normalized_name,
                normalized_name=alias.normalized_name,
                category=alias.category,  # type: ignore[arg-type]
                evidence_source=source,  # type: ignore[arg-type]
                evidence_text=text,
                strength="medium",
                confidence=alias.confidence,
            )
        )
    if not evidence and text.strip():
        evidence.append(
            CandidateEvidence(
                skill=text.strip(),
                normalized_name=_normalize_name(text),
                category=category,
                evidence_source=source,  # type: ignore[arg-type]
                evidence_text=text.strip(),
                strength="weak",
                confidence=confidence,
            )
        )
    return evidence


def _from_job_requirement(item: JobRequirement) -> MatchRequirement:
    return normalize_requirement(
        item.normalized_name or item.text,
        category=item.category,
        importance=item.importance,
        criticality=item.criticality,
        domain=item.domain,
        evidence=item.evidence,
        confidence=item.confidence,
    )


def _first_credential(text: str) -> ProfessionalCredential | None:
    credentials = detect_professional_credentials(text)
    return credentials[0] if credentials else None


def _alias_name(alias: AliasEntry | None, text: str) -> str:
    return alias.normalized_name if alias else _normalize_name(text)


def _normalize_name(text: str) -> str:
    return normalize_text(text).replace(" ", "_")


def _infer_importance(text: str, explicit: str) -> RequirementImportance:
    if explicit in {"required", "preferred", "optional", "unclear"} and explicit != "unclear":
        return explicit  # type: ignore[return-value]
    normalized = normalize_text(text)
    if any(term in normalized for term in REQUIRED_TERMS):
        return "required"
    if any(term in normalized for term in PREFERRED_TERMS):
        return "preferred"
    if any(term in normalized for term in OPTIONAL_TERMS):
        return "optional"
    return "unclear" if explicit == "unclear" else "required"


def _infer_category(
    text: str,
    explicit: str,
    alias: AliasEntry | None,
    credential: ProfessionalCredential | None,
) -> RequirementCategory:
    if credential:
        return credential.category
    if explicit in RequirementCategory.__args__:  # type: ignore[attr-defined]
        return explicit  # type: ignore[return-value]
    if alias and alias.category in RequirementCategory.__args__:  # type: ignore[attr-defined]
        return alias.category  # type: ignore[return-value]
    normalized = normalize_text(text)
    if any(term in normalized for term in ("bacharel", "graduacao", "superior", "tecnico em")):
        return "education"
    if any(term in normalized for term in ("anos", "experiencia")):
        return "experience"
    return "other"


def _infer_criticality(
    explicit: str,
    importance: RequirementImportance,
    credential: ProfessionalCredential | None,
) -> RequirementCriticality:
    if explicit in {"low", "medium", "high", "knockout"} and explicit != "medium":
        return explicit  # type: ignore[return-value]
    if credential and importance == "required":
        return "knockout"
    if credential and importance == "preferred":
        return "medium"
    return "high" if importance == "required" else "medium"


def _matches(requirement: MatchRequirement, evidence: CandidateEvidence) -> bool:
    return (
        requirement.normalized_name.casefold() == evidence.normalized_name.casefold()
        or requirement.normalized_name.casefold() == evidence.skill.casefold()
    )


def _partial_matches(requirement: MatchRequirement, evidence: CandidateEvidence) -> bool:
    req = requirement.normalized_name.casefold().replace("_", " ")
    ev = evidence.normalized_name.casefold().replace("_", " ")
    return bool(
        req and ev and (req in ev or ev in req) and requirement.category == evidence.category
    )


def _missing_gap_severity(requirement: MatchRequirement) -> GapSeverity:
    if requirement.criticality == "knockout":
        return "knockout"
    if requirement.importance == "required":
        return "high"
    if requirement.importance == "preferred":
        return "medium"
    if requirement.importance == "optional":
        return "low"
    return "medium"


def _missing_safe_action(requirement: MatchRequirement, severity: GapSeverity) -> str:
    if requirement.category in {"professional_license", "professional_registration"}:
        return (
            f"A vaga exige {requirement.normalized_name}. Como não há evidência no currículo, "
            f"trate como gap {severity}. Se você possui esse registro ativo, torne essa informação "
            "visível; caso contrário, a vaga pode não ser compatível."
        )
    if severity == "knockout":
        return "Não afirmar esse requisito sem evidência; buscar vaga compatível ou obter a credencial real."
    return "Se for verdadeiro, tornar essa evidência mais clara no currículo."


def _dedupe_requirements(requirements: list[MatchRequirement]) -> list[MatchRequirement]:
    deduped: dict[tuple[str, str], MatchRequirement] = {}
    for requirement in requirements:
        key = (requirement.normalized_name.casefold(), requirement.category)
        deduped.setdefault(key, requirement)
    return list(deduped.values())
