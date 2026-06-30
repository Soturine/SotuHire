"""Formatting helpers for Career Context Engine consumers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import uuid4

from modules.core.text_utils import normalize_text
from modules.memory import CareerEvidence
from modules.memory.schemas import MemoryKind
from modules.profile import ProfileContext, ProfileContextItem

from .models import CareerContext, CareerContextEvidence

if TYPE_CHECKING:
    from modules.github_analyzer.schemas import GitHubAnalyzerReport


def format_context_for_prompt(
    context: CareerContext,
    *,
    include_sensitive: bool = False,
    max_evidence: int = 8,
    max_chars: int = 3_000,
) -> str:
    """Return compact, evidence-aware text for local or explicitly allowed prompts."""
    has_context = any(
        [
            context.profile_summary,
            context.goals,
            context.domains,
            context.seniority,
            context.locations,
            context.work_models,
            context.contract_types,
            context.constraints,
            context.evidence,
        ]
    )
    if not has_context:
        return ""
    lines: list[str] = [f"Proposito: {context.purpose.value}"]
    if context.profile_summary:
        lines.append(f"Resumo: {context.profile_summary}")
    for label, values in [
        ("Objetivos", context.goals),
        ("Areas", context.domains),
        ("Senioridade", context.seniority),
        ("Localidades", context.locations),
        ("Modelos", context.work_models),
        ("Contratos", context.contract_types),
        ("Restricoes", context.constraints),
    ]:
        if values:
            lines.append(f"{label}: {', '.join(values[:8])}")
    evidence_lines = []
    for item in _visible_evidence(context.evidence, include_sensitive=include_sensitive)[
        :max_evidence
    ]:
        status = "confirmado" if item.confirmed_by_user else "a confirmar"
        content = f" - {item.content}" if item.content else ""
        evidence_lines.append(
            f"- {item.title}{content} [{item.kind}; {item.source}; {item.confidence}; {status}]"
        )
    if evidence_lines:
        lines.append("Evidencias:")
        lines.extend(evidence_lines)
    if context.warnings:
        lines.append("Alertas: " + " | ".join(context.warnings[:4]))
    if context.privacy_notes and not include_sensitive:
        lines.append("Privacidade: evidencias sensiveis foram omitidas deste resumo.")
    return "\n".join(lines)[:max_chars].strip()


def context_to_memory_evidence(
    context: CareerContext,
    *,
    include_sensitive: bool = False,
    max_items: int = 12,
) -> list[CareerEvidence]:
    """Convert context evidence to the memory evidence format used by analysis flows."""
    converted: list[CareerEvidence] = []
    for item in _visible_evidence(context.evidence, include_sensitive=include_sensitive)[
        :max_items
    ]:
        converted.append(
            CareerEvidence(
                memory_id=str(item.metadata.get("memory_id") or f"context-{uuid4().hex}"),
                title=item.title,
                source=item.source or "career_context",
                kind=_memory_kind(item.kind),
                excerpt=item.content or item.title,
                relevance_score=max(0.01, item.score),
                selection_reason=f"Career Context Engine: {context.purpose.value}",
            )
        )
    return converted


def context_brief(context: CareerContext, *, max_evidence: int = 3) -> str:
    """Return a short human-readable summary for API metadata and UI hints."""
    parts = []
    if context.goals:
        parts.append("objetivos: " + ", ".join(context.goals[:3]))
    if context.domains:
        parts.append("areas: " + ", ".join(context.domains[:3]))
    if context.locations:
        parts.append("locais: " + ", ".join(context.locations[:3]))
    if context.evidence:
        evidence = [item.title for item in context.evidence if not item.sensitive][:max_evidence]
        if evidence:
            parts.append("evidencias: " + ", ".join(evidence))
    return "; ".join(parts)


def profile_context_from_career_context(context: CareerContext) -> ProfileContext:
    """Adapt unified context back to the existing compact profile context contract."""
    items = [
        ProfileContextItem(
            type=item.kind,
            title=item.title,
            description=item.content or None,
            domain=str(item.metadata.get("domain") or "") or None,
            source=item.source,
            evidence=item.content or item.title,
            confidence=item.confidence,
            confirmed_by_user=item.confirmed_by_user,
        )
        for item in context.evidence
        if not item.sensitive
    ]
    return ProfileContext(
        career_goals=list(context.goals),
        skills=[item for item in items if item.type in {"skill", "technical_skill", "tool"}],
        projects=[
            item
            for item in items
            if item.type
            in {
                "project",
                "portfolio",
                "research_project",
                "portfolio_academic",
                "technical_production",
            }
        ],
        experiences=[item for item in items if "experience" in item.type],
        academic_experiences=[
            item
            for item in items
            if item.type
            in {
                "academic_profile",
                "curriculum_lattes",
                "research_project",
                "extension_project",
                "publication",
                "journal_article",
                "conference_paper",
                "teaching_experience",
                "scientific_initiation",
                "technical_production",
                "portfolio_academic",
            }
        ],
        certifications_and_registries=[
            item
            for item in items
            if item.type in {"certification", "professional_registry", "license"}
        ],
        locations=list(context.locations),
        preferences=[
            *context.domains,
            *context.work_models,
            *context.contract_types,
        ],
        constraints=list(context.constraints),
        application_history_signals=[
            f"Contexto unificado para {context.purpose.value}",
            *context.warnings,
        ],
    )


def profile_evidence_candidates_from_github_report(
    report: GitHubAnalyzerReport,
) -> list[CareerContextEvidence]:
    """Return review-only profile evidence candidates from a GitHub analysis report."""
    candidates: list[CareerContextEvidence] = []
    academic_markers = {
        "academico",
        "acadêmico",
        "pesquisa",
        "artigo",
        "tcc",
        "iniciacao cientifica",
        "iniciação científica",
        "mestrado",
        "doutorado",
        "laboratorio",
        "laboratório",
        "extensao",
        "extensão",
        "dataset",
        "notebook",
        "simulacao",
        "simulação",
        "relatorio tecnico",
        "relatório técnico",
    }
    corpus = normalize_text(
        " ".join(
            [
                report.repository_identity.name,
                report.executive_summary.short_summary,
                report.executive_summary.professional_summary,
                report.executive_summary.recruiter_summary,
                *report.portfolio_value.career_strengths,
                *report.portfolio_value.how_to_present_in_interview,
                *[skill.skill for skill in report.portfolio_value.skills_demonstrated],
            ]
        )
    )
    academic_kind = (
        "portfolio_academic"
        if any(marker in corpus for marker in academic_markers)
        else "portfolio"
    )
    for bullet in report.resume_evidence.safe_resume_bullets[:5]:
        candidates.append(
            CareerContextEvidence(
                title=(
                    "Evidência acadêmica de portfólio GitHub"
                    if academic_kind == "portfolio_academic"
                    else "Evidência de portfólio GitHub"
                ),
                content=bullet.bullet,
                kind=academic_kind,
                source=report.repository_identity.url or "github",
                confidence="high" if bullet.confidence >= 0.75 else "medium",
                confirmed_by_user=False,
                score=bullet.confidence,
                metadata={
                    "review_required": True,
                    "supported_by": bullet.supported_by,
                    "risk_of_overclaiming": bullet.risk_of_overclaiming,
                },
            )
        )
    for skill in report.portfolio_value.skills_demonstrated[:8]:
        candidates.append(
            CareerContextEvidence(
                title=skill.skill,
                content="Skill detectada em arquivos do repositorio; revisar antes de salvar.",
                kind="technical_production" if academic_kind == "portfolio_academic" else "skill",
                source=report.repository_identity.url or "github",
                confidence="high" if skill.confidence >= 0.75 else "medium",
                confirmed_by_user=False,
                score=skill.confidence,
                metadata={
                    "review_required": True,
                    "category": skill.category,
                    "evidence_files": skill.evidence_files,
                },
            )
        )
    for skill in report.resume_evidence.skills_to_add_if_true[:8]:
        candidates.append(
            CareerContextEvidence(
                title=skill,
                content="Skill sugerida pelo GitHub Analyzer; adicionar ao perfil somente se for verdadeira.",
                kind="skill",
                source=report.repository_identity.url or "github",
                confidence="medium",
                confirmed_by_user=False,
                score=0.62,
                metadata={"review_required": True, "source": "skills_to_add_if_true"},
            )
        )
    return _dedupe_candidates(candidates)


def _visible_evidence(
    evidence: list[CareerContextEvidence],
    *,
    include_sensitive: bool,
) -> list[CareerContextEvidence]:
    return [item for item in evidence if include_sensitive or not item.sensitive]


def _memory_kind(kind: str) -> MemoryKind | None:
    aliases = {
        "academic": "education",
        "academic_profile": "education",
        "curriculum_lattes": "education",
        "publication": "project_evidence",
        "journal_article": "project_evidence",
        "conference_paper": "project_evidence",
        "research_project": "project",
        "extension_project": "project",
        "technical_production": "project_evidence",
        "portfolio_academic": "portfolio",
        "teaching_experience": "experience",
    }
    kind = aliases.get(kind, kind)
    allowed: set[MemoryKind] = {
        "resume",
        "project",
        "experience",
        "education",
        "skill",
        "preference",
        "job_analysis",
        "opportunity",
        "feedback",
        "tracker_event",
        "github_profile",
        "github_repo",
        "portfolio",
        "commit_analysis",
        "readme_analysis",
        "project_evidence",
    }
    return cast(MemoryKind, kind) if kind in allowed else None


def _dedupe_candidates(
    candidates: list[CareerContextEvidence],
) -> list[CareerContextEvidence]:
    result: list[CareerContextEvidence] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = normalize_text(" ".join([candidate.title, candidate.content]))
        if key and key not in seen:
            seen.add(key)
            result.append(candidate)
    return result
