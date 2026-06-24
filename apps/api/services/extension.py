"""Adapters between FastAPI web clients and the existing Local Companion service."""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import HTTPException
from modules.local_api import CaptureActionRequest, LocalCompanionService
from modules.parsers.job_description_parser import parse_job_description
from modules.portfolio.schemas import ProjectAnalysisPayload

from apps.api.schemas.extension import (
    ExtensionCaptureItem,
    ExtensionCapturesResponse,
    ExtensionImportGithubResponse,
    ExtensionImportJobResponse,
    ExtensionImportRequest,
    ExtensionImportTrackerResponse,
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
    return ExtensionCapturesResponse(
        captures=[
            ExtensionCaptureItem(
                id=record.id,
                title=record.capture.job_title or record.capture.page_title,
                company=record.capture.company,
                url=record.capture.url,
                domain=record.capture.domain or _domain(record.capture.url),
                kind=_capture_kind(record),
                source=record.capture.collection_method,
                status=record.status,
                tracker_id=record.tracker_id,
                captured_at=record.capture.captured_at,
                updated_at=record.updated_at,
            )
            for record in records
        ]
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
