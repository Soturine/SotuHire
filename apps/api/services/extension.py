"""Adapters between FastAPI web clients and the existing Local Companion service."""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha1
from typing import cast
from urllib.parse import urlparse

from fastapi import HTTPException
from modules.context import CareerContextEngine, CareerContextPurpose, context_brief
from modules.core.text_utils import normalize_text
from modules.local_api import CaptureActionRequest, LocalCompanionService
from modules.parsers.job_description_parser import parse_job_description
from modules.portfolio import ProjectAnalysisStore
from modules.portfolio.schemas import ProjectAnalysisPayload, ProjectAnalysisRecord
from modules.profile.models import ProfileConfidence, ProfileItem
from modules.profile.service import UniversalCareerProfileService

from apps.api.schemas.extension import (
    ExtensionAddToProfileResponse,
    ExtensionCaptureItem,
    ExtensionCapturePatchRequest,
    ExtensionCapturePatchResponse,
    ExtensionCapturesResponse,
    ExtensionContextResponse,
    ExtensionImportGithubResponse,
    ExtensionImportJobResponse,
    ExtensionImportRequest,
    ExtensionImportTrackerResponse,
    ExtensionProfileCandidatesRequest,
    ExtensionProfileCandidatesResponse,
    ExtensionStatusResponse,
)


def extension_status() -> ExtensionStatusResponse:
    """Return status and counts from the local companion capture store."""
    service = LocalCompanionService()
    records = service.capture_store.list()
    last = records[0].updated_at if records else None
    return ExtensionStatusResponse(
        available=True,
        capture_count=len(records),
        last_capture_at=last,
        message=(
            "Local Companion conectado ao backend FastAPI."
            if records
            else "Local Companion disponivel; nenhuma captura local encontrada."
        ),
    )


def extension_captures(limit: int = 20) -> ExtensionCapturesResponse:
    """List recent browser companion captures."""
    service = LocalCompanionService()
    records = service.capture_store.list()[: max(1, min(limit, 100))]
    return ExtensionCapturesResponse(captures=[_capture_item(record) for record in records])


def extension_patch_capture(
    capture_id: str,
    request: ExtensionCapturePatchRequest,
) -> ExtensionCapturePatchResponse:
    """Update only local user-visible status for a companion capture."""
    service = LocalCompanionService()
    record = service.capture_store.get(capture_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Captura nao encontrada.")
    safe_statuses = {"reviewed", "archived", "ignored", "captured", "tracked", "analyzed"}
    status = request.status if request.status in safe_statuses else "reviewed"
    updated = service.capture_store.save(record.model_copy(update={"status": status}))
    item = _capture_item(updated)
    return ExtensionCapturePatchResponse(capture=item, message="Captura atualizada.")


def extension_context() -> ExtensionContextResponse:
    """Return the unified context used by extension/profile bridge actions."""
    context = CareerContextEngine().build(
        CareerContextPurpose.EXTENSION,
        query="capturas da extensao local companion perfil profissional",
        max_evidence=12,
    )
    return ExtensionContextResponse(
        context=context,
        context_summary=context_brief(context),
        message="Contexto local da extensao montado para revisao do Perfil.",
    )


def extension_capture_profile_candidates(
    capture_id: str,
) -> ExtensionProfileCandidatesResponse:
    """Generate review-only ProfileItem candidates from one local capture."""
    record = _capture(capture_id)
    candidates = _profile_candidates_from_capture(record)
    context = CareerContextEngine().build(
        CareerContextPurpose.EXTENSION,
        query=_capture_query(record),
        max_evidence=8,
    )
    return ExtensionProfileCandidatesResponse(
        capture_id=record.id,
        candidates=candidates,
        context_summary=context_brief(context),
        warnings=[
            *context.warnings,
            "Candidatos gerados localmente; revise antes de salvar no Perfil.",
        ],
        message=f"{len(candidates)} candidato(s) de perfil gerado(s) para revisao.",
    )


def extension_capture_add_to_profile(
    capture_id: str,
    request: ExtensionProfileCandidatesRequest,
) -> ExtensionAddToProfileResponse:
    """Persist only the candidates explicitly confirmed by the user."""
    if not request.privacy_acknowledged:
        raise HTTPException(status_code=422, detail="Confirme privacidade antes de salvar.")
    record = _capture(capture_id)
    generated = _profile_candidates_from_capture(record)
    selected, skipped = _selected_candidates(request, generated)
    added = _add_candidates_to_profile(selected, source_ref=record.id)
    return ExtensionAddToProfileResponse(
        capture_id=record.id,
        added=added,
        skipped=skipped,
        message=f"{len(added)} item(ns) confirmado(s) e salvo(s) no Perfil.",
    )


def extension_project_profile_candidates(
    project_id: str,
) -> ExtensionProfileCandidatesResponse:
    """Generate review-only ProfileItem candidates from a saved project analysis."""
    record = _project_record(project_id)
    if record is None:
        capture = _capture(project_id)
        response = extension_capture_profile_candidates(capture.id)
        return response.model_copy(update={"project_id": project_id})
    candidates = _profile_candidates_from_project(record, project_id)
    context = CareerContextEngine().build(
        CareerContextPurpose.GITHUB,
        query=" ".join([record.report.title, record.report.summary, *record.report.stack]),
        max_evidence=8,
    )
    return ExtensionProfileCandidatesResponse(
        project_id=project_id,
        candidates=candidates,
        context_summary=context_brief(context),
        warnings=[
            *context.warnings,
            "Projeto gera candidatos revisaveis; nada foi salvo automaticamente.",
        ],
        message=f"{len(candidates)} candidato(s) de perfil gerado(s) para o projeto.",
    )


def extension_project_add_to_profile(
    project_id: str,
    request: ExtensionProfileCandidatesRequest,
) -> ExtensionAddToProfileResponse:
    """Persist project candidates only after explicit user confirmation."""
    if not request.privacy_acknowledged:
        raise HTTPException(status_code=422, detail="Confirme privacidade antes de salvar.")
    record = _project_record(project_id)
    generated = (
        _profile_candidates_from_project(record, project_id)
        if record is not None
        else _profile_candidates_from_capture(_capture(project_id))
    )
    selected, skipped = _selected_candidates(request, generated)
    added = _add_candidates_to_profile(selected, source_ref=project_id)
    return ExtensionAddToProfileResponse(
        project_id=project_id,
        added=added,
        skipped=skipped,
        message=f"{len(added)} item(ns) de projeto confirmado(s) e salvo(s) no Perfil.",
    )


def extension_import_job(request: ExtensionImportRequest) -> ExtensionImportJobResponse:
    """Parse a captured page as a job and return it to the web frontend."""
    record = _capture(request.capture_id)
    job_text = record.capture.description or record.capture.visible_text
    job = parse_job_description(job_text).model_copy(
        update={
            "title": record.capture.job_title or record.capture.page_title,
            "company": record.capture.company,
            "location": record.capture.location,
            "raw_text": "",
        }
    )
    return ExtensionImportJobResponse(
        capture_id=record.id,
        job=job,
        message="Captura importada para a tela de Vaga.",
    )


def extension_import_tracker(request: ExtensionImportRequest) -> ExtensionImportTrackerResponse:
    """Send a captured job to the existing tracker through LocalCompanionService."""
    if not request.privacy_acknowledged:
        raise HTTPException(status_code=422, detail="Confirme privacidade antes de importar.")
    service = LocalCompanionService()
    try:
        result = service.track_capture(
            CaptureActionRequest(capture_id=request.capture_id, use_ai=request.use_ai)
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Captura nao encontrada.") from exc
    return ExtensionImportTrackerResponse(
        capture_id=result.capture_id,
        tracker_id=result.tracker_id,
        message=result.message,
        provider=result.provider or "local",
    )


def extension_import_github(request: ExtensionImportRequest) -> ExtensionImportGithubResponse:
    """Analyze a GitHub/project capture through the existing companion service."""
    record = _capture(request.capture_id)
    owner, repo = _github_owner_repo(record.capture.url)
    if not owner:
        raise HTTPException(
            status_code=422, detail="A captura nao parece ser um repositorio GitHub."
        )
    service = LocalCompanionService()
    payload = ProjectAnalysisPayload(
        url=record.capture.url,
        owner=owner,
        repo=repo,
        title=record.capture.page_title or repo,
        page_type="github_repo",
        visible_text=record.capture.visible_text or record.capture.description,
        readme_text=record.capture.description,
        files_sampled=["README.md"] if record.capture.description else [],
        analysis_result={"use_github_api": False},
        provider_used="local",
    )
    result = service.analyze_project_capture(payload)
    return ExtensionImportGithubResponse(
        capture_id=record.id,
        report=result.report,
        message=result.message,
    )


def _capture(capture_id: str):
    service = LocalCompanionService()
    record = service.capture_store.get(capture_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Captura nao encontrada.")
    return record


def _capture_item(record) -> ExtensionCaptureItem:
    candidates = _profile_candidates_from_capture(record)
    return ExtensionCaptureItem(
        id=record.id,
        title=record.capture.job_title or record.capture.page_title,
        company=record.capture.company,
        url=record.capture.url,
        domain=record.capture.domain or _domain(record.capture.url),
        kind=_capture_kind(record),
        source=record.capture.collection_method,
        status=record.status,
        tracker_id=record.tracker_id,
        profile_candidate_count=len(candidates),
        context_signal=_context_signal(record, candidates),
        captured_at=record.capture.captured_at,
        updated_at=record.updated_at,
    )


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _github_owner_repo(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.netloc.casefold() not in {"github.com", "www.github.com"}:
        return "", ""
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return "", ""
    return parts[0], parts[1]


def _capture_kind(record) -> str:
    url = record.capture.url
    if _github_owner_repo(url)[0]:
        return "github_repo"
    if record.capture.job_title or record.capture.description:
        return "job"
    if "/in/" in urlparse(url).path.lower():
        return "profile"
    return "other"


def _capture_query(record) -> str:
    capture = record.capture
    return " ".join(
        part
        for part in [
            capture.job_title,
            capture.company,
            capture.location,
            capture.page_title,
            capture.description[:1_000],
            capture.visible_text[:1_000],
        ]
        if part
    )


def _profile_candidates_from_capture(record) -> list[ProfileItem]:
    kind = _capture_kind(record)
    if kind == "github_repo":
        return _project_candidates_from_capture(record, source="github_capture")
    if kind in {"profile", "other"} and "portfolio" in normalize_text(_capture_query(record)):
        return _project_candidates_from_capture(record, source="portfolio_capture")
    return _job_candidates_from_capture(record)


def _job_candidates_from_capture(record) -> list[ProfileItem]:
    capture = record.capture
    text = capture.description or capture.visible_text
    parsed = parse_job_description(text)
    title = parsed.title or capture.job_title or capture.page_title
    source = "extension_capture"
    candidates: list[ProfileItem] = []
    evidence = _short_text(text or title)
    if title:
        candidates.append(
            _candidate(
                record.id,
                item_type="target_role",
                title=title,
                description=(
                    f"Vaga capturada para revisao: {title}"
                    + (f" em {capture.company}." if capture.company else ".")
                ),
                evidence=evidence,
                source=source,
                confidence="medium",
                organization=capture.company or None,
                tags=["extension", "job_capture"],
            )
        )
    location = parsed.location or capture.location
    if location:
        candidates.append(
            _candidate(
                record.id,
                item_type="location_preference",
                title=location,
                description="Localidade observada em captura de vaga; confirmar se e preferencia.",
                evidence=evidence,
                source=source,
                confidence="low",
                tags=["preference", "location"],
            )
        )
    if parsed.modality != "unknown":
        candidates.append(
            _candidate(
                record.id,
                item_type="work_model_preference",
                title=parsed.modality,
                description="Modelo de trabalho observado em captura de vaga; confirmar preferencia.",
                evidence=evidence,
                source=source,
                confidence="low",
                tags=["preference", "work_model"],
            )
        )
    if parsed.contract:
        candidates.append(
            _candidate(
                record.id,
                item_type="contract_preference",
                title=parsed.contract,
                description="Tipo de contrato observado em captura de vaga; confirmar preferencia.",
                evidence=evidence,
                source=source,
                confidence="low",
                tags=["preference", "contract"],
            )
        )
    for skill in parsed.required_skills[:6]:
        candidates.append(
            _candidate(
                record.id,
                item_type="keyword_to_review",
                title=skill,
                description="Requisito da vaga capturada; usar como gap/interesse, nao como habilidade confirmada.",
                evidence=evidence,
                source=source,
                confidence="low",
                tags=["gap", "job_requirement"],
            )
        )
    return _dedupe_profile_items(candidates)


def _project_candidates_from_capture(record, *, source: str) -> list[ProfileItem]:
    capture = record.capture
    text = capture.description or capture.visible_text
    owner, repo = _github_owner_repo(capture.url)
    title = repo or capture.page_title or capture.job_title or _domain(capture.url)
    candidates = [
        _candidate(
            record.id,
            item_type="portfolio" if source == "portfolio_capture" else "project",
            title=title,
            description="Projeto capturado pela extensao; revise autoria e escopo antes de confirmar.",
            evidence=_short_text(text or capture.url),
            source=source,
            confidence="medium",
            tags=["extension", "project"],
            skills=_skills_from_text(text),
        )
    ]
    for skill in _skills_from_text(text)[:8]:
        candidates.append(
            _candidate(
                record.id,
                item_type="technical_skill",
                title=skill,
                description="Skill detectada no projeto capturado; confirmar antes de salvar.",
                evidence=_short_text(text),
                source=source,
                confidence="medium",
                tags=["project_skill"],
            )
        )
    if owner:
        candidates[0] = candidates[0].model_copy(update={"organization": owner})
    return _dedupe_profile_items(candidates)


def _profile_candidates_from_project(
    record: ProjectAnalysisRecord,
    project_id: str,
) -> list[ProfileItem]:
    report = record.report
    source = "github_capture" if report.page_type.startswith("github") else "portfolio_capture"
    evidence = _short_text(" ".join([report.summary, *report.strengths, *report.resume_highlights]))
    candidates = [
        _candidate(
            project_id,
            item_type="portfolio" if report.page_type == "portfolio" else "project",
            title=report.title or report.repo or report.url,
            description=report.summary or "Projeto analisado localmente pelo SotuHire.",
            evidence=evidence,
            source=source,
            confidence="high" if report.overall_score >= 75 else "medium",
            organization=report.owner or None,
            skills=_unique([*report.stack, *report.technical_keywords])[:20],
            tags=["project_analysis", report.grade],
        )
    ]
    for skill in _unique([*report.stack, *report.technical_keywords])[:10]:
        candidates.append(
            _candidate(
                project_id,
                item_type="technical_skill",
                title=skill,
                description="Skill detectada em analise local de projeto; confirmar antes de salvar.",
                evidence=evidence,
                source=source,
                confidence="high" if report.overall_score >= 75 else "medium",
                tags=["project_skill"],
            )
        )
    return _dedupe_profile_items(candidates)


def _candidate(
    source_ref: str,
    *,
    item_type: str,
    title: str,
    description: str,
    evidence: str,
    source: str,
    confidence: str,
    organization: str | None = None,
    skills: Iterable[str] = (),
    tags: Iterable[str] = (),
) -> ProfileItem:
    confidence_value = cast(
        ProfileConfidence,
        confidence if confidence in {"low", "medium", "high"} else "medium",
    )
    return ProfileItem(
        item_id=_candidate_id(source_ref, item_type, title),
        type=item_type,
        title=title[:240],
        description=description[:5_000],
        organization=organization,
        tags=_unique(tags),
        skills=_unique(skills),
        evidence=evidence[:5_000] or title[:240],
        source=source,
        source_ref=source_ref,
        confidence=confidence_value,
        confirmed_by_user=False,
    )


def _selected_candidates(
    request: ExtensionProfileCandidatesRequest,
    generated: list[ProfileItem],
) -> tuple[list[ProfileItem], list[str]]:
    source = request.items or generated
    if not request.candidate_ids:
        return _dedupe_profile_items(source), []
    by_id = {item.item_id: item for item in source}
    selected: list[ProfileItem] = []
    skipped: list[str] = []
    for candidate_id in request.candidate_ids:
        item = by_id.get(candidate_id)
        if item is None:
            skipped.append(candidate_id)
        else:
            selected.append(item)
    return _dedupe_profile_items(selected), skipped


def _add_candidates_to_profile(
    candidates: list[ProfileItem],
    *,
    source_ref: str,
) -> list[ProfileItem]:
    service = UniversalCareerProfileService()
    added = []
    for item in candidates:
        source = item.source if item.source in _ALLOWED_PROFILE_SOURCES else "extension_capture"
        saved = service.add_item(
            item.model_copy(
                update={
                    "source": source,
                    "source_ref": item.source_ref or source_ref,
                    "confirmed_by_user": True,
                    "sensitive": item.sensitive,
                }
            ),
            confirmed_by_user=True,
        )
        added.append(saved)
    return added


def _project_record(project_id: str) -> ProjectAnalysisRecord | None:
    records = ProjectAnalysisStore().list()
    normalized = normalize_text(project_id)
    for record in records:
        if record.report.id == project_id:
            return record
        if normalize_text(record.payload.url) == normalized:
            return record
        if normalize_text(record.report.url) == normalized:
            return record
    return None


def _context_signal(record, candidates: list[ProfileItem]) -> str:
    if not candidates:
        return "Sem candidatos de perfil detectados."
    kind = _capture_kind(record)
    if kind == "github_repo":
        return "Projeto pode gerar evidencias revisaveis para o Perfil."
    if any(item.type == "target_role" for item in candidates):
        return "Vaga pode atualizar objetivos, preferencias ou gaps revisaveis."
    return "Captura pode contribuir com contexto apos revisao."


def _candidate_id(source_ref: str, item_type: str, title: str) -> str:
    digest = sha1(f"{source_ref}|{item_type}|{normalize_text(title)}".encode()).hexdigest()
    return f"candidate_{digest[:16]}"


def _short_text(text: str, *, limit: int = 600) -> str:
    return " ".join(str(text or "").split())[:limit]


def _skills_from_text(text: str) -> list[str]:
    normalized = normalize_text(text)
    known = {
        "python": "Python",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "sql": "SQL",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "react": "React",
        "typescript": "TypeScript",
        "javascript": "JavaScript",
        "node": "Node.js",
        "docker": "Docker",
        "pytest": "Pytest",
        "excel": "Excel",
        "power bi": "Power BI",
        "autocad": "AutoCAD",
    }
    return _unique(label for needle, label in known.items() if needle in normalized)


def _dedupe_profile_items(items: Iterable[ProfileItem]) -> list[ProfileItem]:
    result: list[ProfileItem] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item.type, normalize_text(item.title))
        if item.title and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value or "").strip()
        key = normalize_text(cleaned)
        if cleaned and key and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


_ALLOWED_PROFILE_SOURCES = {
    "extension_capture",
    "github_capture",
    "portfolio_capture",
    "browser_assisted_capture",
}
