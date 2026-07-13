"""Local data health, backup, export and guarded restore endpoints."""

from __future__ import annotations

import sqlite3
import zipfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.data import (
    DataArchiveResponse,
    DataArchivesResponse,
    DataBackupCreateRequest,
    DataHealthResponse,
    DataRestoreRequest,
    DataRestoreResponse,
)
from apps.api.services.data import (
    DataArchiveError,
    create_data_archive,
    data_health,
    list_data_archives,
    resolve_data_archive,
    restore_data,
)

router = APIRouter(prefix="/api/v1/data", tags=["data-reliability"])


@router.get("/health", response_model=ApiEnvelope[DataHealthResponse])
def get_data_health() -> ApiEnvelope[DataHealthResponse]:
    """Run a read-only integrity scan over SQLite and legacy stores."""
    return ok(data_health())


@router.get("/backups", response_model=ApiEnvelope[DataArchivesResponse])
def get_data_archives() -> ApiEnvelope[DataArchivesResponse]:
    """List valid archives managed by the local API."""
    return ok(list_data_archives())


@router.post("/backups", response_model=ApiEnvelope[DataArchiveResponse])
def post_data_archive(
    payload: DataBackupCreateRequest,
) -> ApiEnvelope[DataArchiveResponse]:
    """Create a checksummed backup or portable export without secrets."""
    try:
        return ok(create_data_archive(payload.kind))
    except (OSError, sqlite3.DatabaseError, ValueError, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=400, detail=_safe_error(exc)) from exc


@router.get("/backups/{archive_name}", response_class=FileResponse)
def download_data_archive(archive_name: str) -> FileResponse:
    """Download one archive from the server-managed backup directory."""
    try:
        archive = resolve_data_archive(archive_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataArchiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FileResponse(
        archive,
        media_type="application/zip",
        filename=archive.name,
        headers={"Cache-Control": "no-store"},
    )


@router.post("/restore", response_model=ApiEnvelope[DataRestoreResponse])
def post_data_restore(
    payload: DataRestoreRequest,
) -> ApiEnvelope[DataRestoreResponse]:
    """Validate by default and apply only after explicit confirmation."""
    try:
        return ok(restore_data(payload))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (DataArchiveError, ValueError, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=400, detail=_safe_error(exc)) from exc


def _safe_error(exc: BaseException) -> str:
    """Return user-actionable errors without local paths or trace details."""
    if isinstance(exc, DataArchiveError):
        return str(exc)
    if isinstance(exc, zipfile.BadZipFile):
        return "Arquivo ZIP inválido."
    return "Não foi possível validar o arquivo de dados."
