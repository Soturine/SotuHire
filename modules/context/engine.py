"""Career Context Engine orchestration."""

from __future__ import annotations

from collections.abc import Iterable

from modules.core.text_utils import normalize_text
from modules.memory import CareerMemoryQuery, MemoryRetriever
from modules.memory.schemas import CareerEvidence
from modules.profile import ProfileContext, ProfileContextItem, ProfileContextOrchestrator

from .models import CareerContext, CareerContextEvidence, CareerContextPurpose


class CareerContextEngine:
    """Build compact local-first context for SotuHire workflows."""

    def __init__(
        self,
        *,
        profile_orchestrator: ProfileContextOrchestrator | None = None,
        memory_retriever: MemoryRetriever | None = None,
    ) -> None:
        self.profile_orchestrator = profile_orchestrator or ProfileContextOrchestrator()
        self.memory_retriever = memory_retriever or MemoryRetriever()

    def build(
        self,
        purpose: CareerContextPurpose | str,
        query: str = "",
        include_memory: bool = True,
        include_tracker: bool = True,
        include_sources: bool = True,
        include_extension: bool = True,
        include_github: bool = True,
        max_evidence: int = 12,
        profile_context_override: dict[str, object] | None = None,
    ) -> CareerContext:
        """Build a serializable context without inventing facts."""
        resolved_purpose = _purpose(purpose)
        warnings: list[str] = []
        privacy_notes = [
            "Contexto local-first; revise antes de compartilhar com providers externos.",
            "Dados sensiveis devem permanecer locais sem permissao explicita.",
        ]
        profile_context = self._profile_context(
            resolved_purpose,
            profile_context_override=profile_context_override,
            warnings=warnings,
        )
        profile_evidence = _profile_evidence(profile_context)
        memory_evidence: list[CareerContextEvidence] = []
        if include_memory:
            memory_evidence = self._memory_evidence(
                purpose=resolved_purpose,
                query=_context_query(resolved_purpose, query, profile_context),
                include_tracker=include_tracker,
                include_sources=include_sources,
                include_extension=include_extension,
                include_github=include_github,
                max_evidence=max(1, max_evidence),
                warnings=warnings,
            )

        evidence = _dedupe_evidence([*profile_evidence, *memory_evidence])
        evidence = sorted(evidence, key=_evidence_sort_key, reverse=True)[:max_evidence]
        if not evidence:
            warnings.append("Nenhuma evidencia local foi encontrada; use revisao manual.")
        if any(item.sensitive for item in evidence):
            privacy_notes.append(
                "Ha evidencias sensiveis; nao envie a provider externo sem revisar."
            )

        return CareerContext(
            purpose=resolved_purpose,
            profile_summary=_profile_summary(profile_context),
            goals=_unique(profile_context.career_goals),
            domains=_domains(profile_context),
            seniority=_seniority(profile_context),
            locations=_unique(profile_context.locations),
            work_models=_work_models(profile_context),
            contract_types=_contract_types(profile_context),
            constraints=_unique(profile_context.constraints),
            evidence=evidence,
            warnings=_unique(warnings),
            privacy_notes=_unique(privacy_notes),
        )

    def _profile_context(
        self,
        purpose: CareerContextPurpose,
        *,
        profile_context_override: dict[str, object] | None,
        warnings: list[str],
    ) -> ProfileContext:
        try:
            return self.profile_orchestrator.build_context(
                purpose=purpose.value,
                override=profile_context_override,
            )
        except Exception:
            warnings.append("Perfil local indisponivel; contexto foi montado sem perfil salvo.")
            return ProfileContext()

    def _memory_evidence(
        self,
        *,
        purpose: CareerContextPurpose,
        query: str,
        include_tracker: bool,
        include_sources: bool,
        include_extension: bool,
        include_github: bool,
        max_evidence: int,
        warnings: list[str],
    ) -> list[CareerContextEvidence]:
        try:
            retrieved = self.memory_retriever.retrieve(
                CareerMemoryQuery(query=query, top_k=min(20, max_evidence * 2))
            )
        except Exception:
            warnings.append("Memoria local indisponivel; RAG lexical ignorado nesta montagem.")
            return []
        allowed = _allowed_memory_kinds(
            purpose,
            include_tracker=include_tracker,
            include_sources=include_sources,
            include_github=include_github,
        )
        converted = [
            _evidence_from_memory(item)
            for item in retrieved
            if item.kind is None or not allowed or item.kind in allowed
            if include_extension or not _is_extension_memory(item)
        ]
        return converted[:max_evidence]


def _purpose(value: CareerContextPurpose | str) -> CareerContextPurpose:
    if isinstance(value, CareerContextPurpose):
        return value
    try:
        return CareerContextPurpose(value)
    except ValueError:
        return CareerContextPurpose.GENERIC


def _profile_evidence(context: ProfileContext) -> list[CareerContextEvidence]:
    evidence: list[CareerContextEvidence] = []
    for bucket, items in [
        ("education", context.education),
        ("experience", context.experiences),
        ("academic", context.academic_experiences),
        ("project", context.projects),
        ("certification", context.certifications_and_registries),
        ("skill", context.skills),
        ("language", context.languages),
    ]:
        evidence.extend(_evidence_from_profile_item(item, bucket) for item in items)
    evidence.extend(
        CareerContextEvidence(
            title=constraint,
            kind="constraint",
            source="profile",
            confidence="high",
            confirmed_by_user=True,
            score=0.92,
        )
        for constraint in context.constraints
    )
    return evidence


def _evidence_from_profile_item(item: ProfileContextItem, bucket: str) -> CareerContextEvidence:
    source = item.source or "profile"
    return CareerContextEvidence(
        title=item.title,
        content=item.description or item.evidence or "",
        kind=item.type or bucket,
        source=source,
        confidence=item.confidence,
        confirmed_by_user=item.confirmed_by_user,
        sensitive=item.sensitive
        or _is_sensitive(item.title, item.description or "", item.evidence or "", source),
        score=_profile_score(item),
        metadata={
            "bucket": bucket,
            "area": item.area or "",
            "domain": item.domain or "",
        },
    )


def _evidence_from_memory(item: CareerEvidence) -> CareerContextEvidence:
    confidence = "high" if item.relevance_score >= 0.78 else "medium"
    return CareerContextEvidence(
        title=item.title,
        content=item.excerpt,
        kind=item.kind or "memory",
        source=item.source or "memory",
        confidence=confidence,
        confirmed_by_user=False,
        sensitive=_is_sensitive(item.title, item.excerpt, item.source),
        score=item.relevance_score,
        metadata={
            "memory_id": item.memory_id,
            "selection_reason": item.selection_reason,
            "score_breakdown": item.score_breakdown,
        },
    )


def _context_query(
    purpose: CareerContextPurpose,
    query: str,
    profile_context: ProfileContext,
) -> str:
    parts = [
        purpose.value,
        query,
        " ".join(profile_context.career_goals),
        " ".join(profile_context.preferences),
        " ".join(profile_context.locations),
        " ".join(profile_context.application_history_signals),
    ]
    profile_titles = [
        item.title
        for item in [
            *profile_context.skills,
            *profile_context.projects,
            *profile_context.experiences,
            *profile_context.academic_experiences,
            *profile_context.education,
            *profile_context.certifications_and_registries,
        ]
    ]
    parts.append(" ".join(profile_titles[:20]))
    return " ".join(part for part in parts if part).strip() or purpose.value


def _allowed_memory_kinds(
    purpose: CareerContextPurpose,
    *,
    include_tracker: bool,
    include_sources: bool,
    include_github: bool,
) -> set[str]:
    base = {
        "resume",
        "project",
        "experience",
        "education",
        "skill",
        "preference",
        "job_analysis",
        "feedback",
        "academic",
        "lattes",
        "publication",
        "research_project",
        "extension_project",
        "teaching_experience",
        "technical_production",
    }
    if include_tracker:
        base.update({"tracker_event", "opportunity"})
    if include_sources:
        base.update({"opportunity"})
    if include_github:
        base.update({"github_profile", "github_repo", "portfolio", "project_evidence"})
    if purpose == CareerContextPurpose.GITHUB:
        base.update({"commit_analysis", "readme_analysis", "portfolio_academic"})
    if purpose == CareerContextPurpose.EXTENSION:
        base.update({"opportunity", "project", "portfolio", "github_repo", "project_evidence"})
    if purpose in {
        CareerContextPurpose.ACADEMIC,
        CareerContextPurpose.LATTES,
        CareerContextPurpose.PUBLIC_EXAMS,
    }:
        base.update(
            {
                "academic_profile",
                "curriculum_lattes",
                "education",
                "research_project",
                "publication",
                "journal_article",
                "conference_paper",
                "technical_production",
                "teaching_experience",
                "scholarship",
                "grant",
            }
        )
    return base


def _is_extension_memory(item: CareerEvidence) -> bool:
    source = normalize_text(item.source)
    markers = {
        "extension_capture",
        "browser_assisted_capture",
        "companion_capture",
        "github_capture",
        "portfolio_capture",
    }
    return any(marker in source for marker in markers)


def _profile_summary(context: ProfileContext) -> str:
    identity = context.identity
    summary = str(identity.get("summary") or "").strip()
    headline = str(identity.get("headline") or "").strip()
    if summary and headline:
        return f"{headline}. {summary}"
    if summary or headline:
        return summary or headline
    if context.career_goals:
        return "Objetivos: " + ", ".join(context.career_goals[:5])
    return ""


def _domains(context: ProfileContext) -> list[str]:
    values = []
    values.extend(_metadata_values(context, "domain"))
    values.extend(context.preferences)
    return _unique(values)


def _seniority(context: ProfileContext) -> list[str]:
    labels = ("estagio", "junior", "pleno", "senior", "trainee", "aprendiz")
    corpus = normalize_text(" ".join([*context.application_history_signals, *context.preferences]))
    return [label for label in labels if label in corpus]


def _work_models(context: ProfileContext) -> list[str]:
    labels = ("remoto", "hibrido", "presencial")
    corpus = normalize_text(" ".join([*context.preferences, *context.locations]))
    return [label for label in labels if label in corpus]


def _contract_types(context: ProfileContext) -> list[str]:
    labels = ("clt", "pj", "estagio", "trainee", "bolsa", "temporario")
    corpus = normalize_text(" ".join(context.preferences))
    return [
        label.upper() if label in {"clt", "pj"} else label for label in labels if label in corpus
    ]


def _metadata_values(context: ProfileContext, key: str) -> list[str]:
    values = []
    for item in [
        *context.education,
        *context.experiences,
        *context.academic_experiences,
        *context.projects,
        *context.certifications_and_registries,
        *context.skills,
        *context.languages,
    ]:
        value = getattr(item, key, None)
        if value:
            values.append(str(value))
    return values


def _dedupe_evidence(items: Iterable[CareerContextEvidence]) -> list[CareerContextEvidence]:
    best_by_key: dict[str, CareerContextEvidence] = {}
    for item in items:
        key = _dedupe_key(item)
        current = best_by_key.get(key)
        if current is None or _evidence_sort_key(item) > _evidence_sort_key(current):
            best_by_key[key] = item
    return list(best_by_key.values())


def _dedupe_key(item: CareerContextEvidence) -> str:
    return normalize_text(" ".join([item.title, item.content[:180]]))


def _evidence_sort_key(item: CareerContextEvidence) -> tuple[int, int, float, int]:
    confidence = {"low": 1, "medium": 2, "high": 3}[item.confidence]
    return (
        int(item.confirmed_by_user),
        confidence,
        item.score,
        0 if item.sensitive else 1,
    )


def _profile_score(item: ProfileContextItem) -> float:
    base = {"low": 0.45, "medium": 0.68, "high": 0.86}[item.confidence]
    if item.confirmed_by_user:
        base += 0.1
    if item.evidence:
        base += 0.04
    return round(min(1.0, base), 2)


def _is_sensitive(*parts: str) -> bool:
    text = normalize_text(" ".join(parts))
    markers = {
        "cpf",
        "rg",
        "cnpj",
        "telefone",
        "phone",
        "endereco",
        "address",
        "salario",
        "salary",
        "doenca",
        "diagnostico",
        "deficiencia",
        "pcd",
        "token",
        "cookie",
        "session",
    }
    return any(marker in text for marker in markers)


def _unique(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = str(item).strip()
        key = normalize_text(cleaned)
        if cleaned and key and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result
