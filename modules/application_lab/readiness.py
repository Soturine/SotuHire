"""Deterministic, multi-domain application-readiness rules."""

from __future__ import annotations

import re
from typing import Any, Literal

from modules.application_lab.models import (
    ApplicationReadinessReport,
    MasterResume,
    ReadinessDimension,
    ReadinessPerspective,
)
from modules.core.text_utils import normalize_text
from modules.storage.snapshots import JobSnapshot

DIMENSION_WEIGHTS: dict[str, float] = {
    "resume": 0.10,
    "education": 0.10,
    "experience": 0.15,
    "skills": 0.15,
    "projects": 0.08,
    "portfolio": 0.05,
    "academic": 0.05,
    "certifications": 0.035,
    "professional_registrations": 0.035,
    "languages": 0.05,
    "github": 0.05,
    "requirements": 0.15,
}

DIMENSION_LABELS = {
    "resume": "Currículo",
    "education": "Formação",
    "experience": "Experiência",
    "skills": "Competências",
    "projects": "Projetos",
    "portfolio": "Portfólio",
    "academic": "Lattes/Produção acadêmica",
    "certifications": "Certificações",
    "professional_registrations": "Registros profissionais",
    "languages": "Idiomas",
    "github": "GitHub",
    "requirements": "Requisitos da vaga",
}

SECTION_ALIASES = {
    "education": {"education", "formacao", "academic_education"},
    "experience": {"experience", "experiencia", "work_experience"},
    "skills": {"skills", "competencias", "habilidades"},
    "projects": {"projects", "projetos"},
    "portfolio": {"portfolio", "portfolio_projects"},
    "academic": {"academic", "lattes", "publications", "research", "producao_academica"},
    "certifications": {
        "certifications",
        "certificacoes",
    },
    "professional_registrations": {
        "professional_registry",
        "professional_registrations",
        "registrations",
        "registros_profissionais",
    },
    "languages": {"languages", "idiomas"},
    "github": {"github"},
}

TECH_MARKERS = {
    "api",
    "backend",
    "cloud",
    "dados",
    "data",
    "devops",
    "desenvolvedor",
    "developer",
    "frontend",
    "github",
    "machine learning",
    "python",
    "software",
    "tecnologia",
}


def build_readiness_report(
    session_id: str,
    master_resume: MasterResume,
    job_snapshot: JobSnapshot,
) -> ApplicationReadinessReport:
    """Calculate a transparent score; AI never chooses or modifies the score."""
    resume_text = _resume_text(master_resume)
    job_text = " ".join(
        [
            job_snapshot.title,
            job_snapshot.description,
            job_snapshot.raw_text,
            _stringify(job_snapshot.structured_data),
        ]
    )
    section_map = _sections(master_resume)
    requirements = _requirements(job_snapshot)
    requirement_hits = [item for item in requirements if _requirement_present(item, resume_text)]
    requirement_coverage = len(requirement_hits) / len(requirements) if requirements else 0.0
    evidence_total, evidence_confirmed = _evidence_counts(master_resume)
    evidence_coverage = evidence_confirmed / evidence_total if evidence_total else 0.0
    github_applicable = _github_relevant(job_text, master_resume.target_role)

    coverages: dict[str, float | None] = {
        "resume": min(
            1.0,
            0.25 * bool(master_resume.summary.strip())
            + 0.25 * bool(master_resume.raw_text.strip() or master_resume.sections)
            + 0.25 * bool(section_map.get("education") or section_map.get("experience"))
            + 0.25 * bool(section_map.get("skills")),
        ),
        "education": _section_coverage(section_map, "education"),
        "experience": _section_coverage(section_map, "experience"),
        "skills": _section_coverage(section_map, "skills"),
        "projects": _section_coverage(section_map, "projects"),
        "portfolio": _section_coverage(section_map, "portfolio"),
        "academic": _section_coverage(section_map, "academic"),
        "certifications": _section_coverage(section_map, "certifications"),
        "professional_registrations": _section_coverage(section_map, "professional_registrations"),
        "languages": _section_coverage(section_map, "languages"),
        "github": _section_coverage(section_map, "github") if github_applicable else None,
        "requirements": requirement_coverage,
    }
    applicable_weight = sum(
        DIMENSION_WEIGHTS[key] for key, coverage in coverages.items() if coverage is not None
    )
    weighted = sum(
        DIMENSION_WEIGHTS[key] * coverage
        for key, coverage in coverages.items()
        if coverage is not None
    )
    score = round(100 * weighted / applicable_weight, 1) if applicable_weight else 0.0
    dimensions = {
        key: ReadinessDimension(
            dimension=key,
            label=DIMENSION_LABELS[key],
            status=_status(coverage),
            coverage=round(coverage, 3) if coverage is not None else None,
            weight=round(DIMENSION_WEIGHTS[key] / applicable_weight, 3)
            if coverage is not None and applicable_weight
            else 0,
            evidence_count=_dimension_evidence(section_map, key),
            explanation=_dimension_explanation(key, coverage, requirements, requirement_hits),
        )
        for key, coverage in coverages.items()
    }
    strengths = [dimension.label for dimension in dimensions.values() if dimension.status == "met"]
    blockers = _blockers(dimensions, requirements, requirement_hits)
    missing = [
        dimension.label
        for dimension in dimensions.values()
        if dimension.status == "missing" and dimension.dimension != "requirements"
    ]
    unsupported = _unsupported_claim_risks(master_resume)
    warnings = [
        "Readiness é uma medida de cobertura e preparação; não é probabilidade de entrevista."
    ]
    if not requirements:
        warnings.append(
            "A vaga não trouxe requisitos estruturados suficientes para cobertura completa."
        )
    if not github_applicable:
        warnings.append("GitHub marcado como not_applicable para esta vaga/área.")
    if evidence_coverage < 0.5:
        warnings.append("Menos da metade das entradas possui confirmação ou referência de origem.")
    recommended = _recommended_edits(dimensions, blockers)
    perspectives = _perspectives(dimensions, blockers, unsupported)
    evidence_used: list[str | dict[str, Any]] = list(
        dict.fromkeys(
            [*master_resume.source_refs, *job_snapshot.source_refs]
            + [
                ref
                for section in master_resume.sections
                for entry in section.entries
                for ref in entry.source_refs
            ]
        )
    )
    return ApplicationReadinessReport(
        session_id=session_id,
        readiness_score=score,
        score_explanation=(
            "Média ponderada e renormalizada das dimensões aplicáveis; requisitos e evidências "
            "são calculados deterministicamente. GitHub não penaliza áreas onde não é relevante."
        ),
        evidence_coverage=round(evidence_coverage, 3),
        requirement_coverage=round(requirement_coverage, 3),
        source_dimensions=dimensions,
        strengths=strengths,
        top_blockers=blockers[:5],
        missing_information=missing,
        unsupported_claim_risks=unsupported,
        recommended_edits=recommended,
        copy_ready_snippets=[master_resume.summary] if master_resume.summary.strip() else [],
        action_plan_preview=[f"Revisar: {item}" for item in blockers[:3]],
        warnings=warnings,
        provider_metadata={
            "analysis_mode": "deterministic_local",
            "provider_requested": "local",
            "provider_used": "local",
            "fallback_used": False,
            "degraded_mode": False,
            "perspective_execution": "uma análise consolidada em três perspectivas",
        },
        evidence_used=evidence_used,
        perspectives=perspectives,
    )


def _resume_text(resume: MasterResume) -> str:
    values = [resume.title, resume.target_role, resume.summary, resume.raw_text]
    for section in resume.sections:
        if not section.enabled:
            continue
        values.extend([section.title, section.content])
        for entry in section.entries:
            if entry.enabled:
                values.extend([entry.title, entry.subtitle, entry.content])
    return normalize_text(" ".join(values))


def _sections(resume: MasterResume) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    for section in resume.sections:
        if not section.enabled:
            continue
        normalized = normalize_text(section.section_type)
        matched = next(
            (key for key, aliases in SECTION_ALIASES.items() if normalized in aliases),
            normalized or "other",
        )
        result.setdefault(matched, []).append(section)
    return result


def _section_coverage(section_map: dict[str, list[Any]], key: str) -> float:
    sections = section_map.get(key, [])
    if not sections:
        return 0.0
    entries = sum(
        sum(
            entry.enabled and bool((entry.content or entry.title).strip())
            for entry in section.entries
        )
        for section in sections
    )
    has_content = any(section.content.strip() for section in sections)
    return (
        1.0
        if entries >= 2 or (entries >= 1 and has_content)
        else 0.6
        if entries or has_content
        else 0.3
    )


def _requirements(job: JobSnapshot) -> list[str]:
    data = job.structured_data
    values: list[str] = []
    for key in (
        "requirements",
        "required_skills",
        "mandatory_requirements",
        "qualifications",
        "preferred_requirements",
    ):
        nested = data.get(key)
        if isinstance(nested, list):
            values.extend(_requirement_text(item) for item in nested)
        elif isinstance(nested, str):
            values.extend(re.split(r"[\n;•]+", nested))
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def _requirement_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("name", "requirement", "description", "skill"):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested
    return ""


def _requirement_present(requirement: str, resume_text: str) -> bool:
    normalized = normalize_text(requirement)
    if normalized and normalized in resume_text:
        return True
    tokens = {token for token in normalized.split() if len(token) >= 4}
    resume_tokens = set(resume_text.split())
    return bool(tokens) and len(tokens & resume_tokens) / len(tokens) >= 0.75


def _evidence_counts(resume: MasterResume) -> tuple[int, int]:
    entries = [entry for section in resume.sections for entry in section.entries if entry.enabled]
    confirmed = sum(bool(entry.confirmed_by_user or entry.source_refs) for entry in entries)
    return len(entries), confirmed


def _github_relevant(job_text: str, target_role: str) -> bool:
    corpus = normalize_text(f"{job_text} {target_role}")
    return any(marker in corpus for marker in TECH_MARKERS)


def _status(
    coverage: float | None,
) -> Literal["met", "partial", "missing", "not_applicable"]:
    if coverage is None:
        return "not_applicable"
    if coverage >= 0.8:
        return "met"
    if coverage > 0:
        return "partial"
    return "missing"


def _dimension_evidence(section_map: dict[str, list[Any]], key: str) -> int:
    if key in {"resume", "requirements"}:
        return 0
    return sum(len(section.entries) for section in section_map.get(key, []))


def _dimension_explanation(
    key: str,
    coverage: float | None,
    requirements: list[str],
    hits: list[str],
) -> str:
    if coverage is None:
        return "Dimensão não aplicável à vaga atual."
    if key == "requirements":
        return f"{len(hits)} de {len(requirements)} requisitos tiveram evidência textual."
    return {
        "met": "Conteúdo suficiente e habilitado no currículo mestre.",
        "partial": "Conteúdo presente, mas ainda incompleto ou pouco detalhado.",
        "missing": "Nenhum conteúdo confirmado foi encontrado nesta dimensão.",
        "not_applicable": "Dimensão não aplicável.",
    }[_status(coverage)]


def _blockers(
    dimensions: dict[str, ReadinessDimension], requirements: list[str], hits: list[str]
) -> list[str]:
    blockers = [
        f"{item.label}: informação ausente"
        for item in dimensions.values()
        if item.status == "missing" and item.weight >= 0.08
    ]
    missing_requirements = [item for item in requirements if item not in hits]
    blockers.extend(f"Requisito sem evidência: {item}" for item in missing_requirements[:5])
    return list(dict.fromkeys(blockers))


def _unsupported_claim_risks(resume: MasterResume) -> list[str]:
    risks: list[str] = []
    for section in resume.sections:
        for entry in section.entries:
            if (
                entry.enabled
                and entry.content.strip()
                and not (entry.confirmed_by_user or entry.source_refs)
            ):
                risks.append(f"{section.title}: {entry.title or 'entrada sem título'}")
    return risks[:20]


def _recommended_edits(dimensions: dict[str, ReadinessDimension], blockers: list[str]) -> list[str]:
    edits = [
        f"Completar a seção {item.label} com fatos confirmados."
        for item in dimensions.values()
        if item.status in {"missing", "partial"} and item.dimension != "requirements"
    ]
    edits.extend(
        f"Revisar evidência para {item}." for item in blockers if item.startswith("Requisito")
    )
    return edits[:10]


def _perspectives(
    dimensions: dict[str, ReadinessDimension],
    blockers: list[str],
    unsupported: list[str],
) -> dict[str, ReadinessPerspective]:
    return {
        "structure_ats": ReadinessPerspective(
            perspective_id="structure_ats",
            label="Estrutura e ATS",
            summary="Cobertura de estrutura e requisitos calculada por regras locais.",
            findings=[
                dimensions["resume"].explanation,
                dimensions["requirements"].explanation,
            ],
        ),
        "narrative_positioning": ReadinessPerspective(
            perspective_id="narrative_positioning",
            label="Narrativa e posicionamento",
            summary="Clareza do resumo, experiências e projetos para o alvo selecionado.",
            findings=blockers[:3] or ["Nenhum bloqueador narrativo prioritário."],
        ),
        "evidence_differentiators": ReadinessPerspective(
            perspective_id="evidence_differentiators",
            label="Evidências e diferenciais",
            summary="Confirmação e proveniência das afirmações usadas na candidatura.",
            findings=unsupported[:3] or ["Não foram detectadas afirmações habilitadas sem origem."],
        ),
    }


def _stringify(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_stringify(nested)}" for key, nested in value.items())
    if isinstance(value, list):
        return " ".join(_stringify(item) for item in value)
    return str(value or "")


__all__ = ["DIMENSION_WEIGHTS", "build_readiness_report"]
