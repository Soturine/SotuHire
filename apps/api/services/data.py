"""Secret-safe application service for local data reliability operations."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Literal

from modules.storage.backup import (
    BackupManifest,
    BackupResult,
    create_backup,
    restore_backup,
)
from modules.storage.database import default_data_dir
from modules.storage.health import check_data_health

from apps.api.schemas.data import (
    DataArchiveResponse,
    DataArchivesResponse,
    DataHealthIssueResponse,
    DataHealthResponse,
    DataRestoreRequest,
    DataRestoreResponse,
)

RESTORE_CONFIRMATION = "RESTAURAR"
ARCHIVE_PREFIXES = ("sotuhire-data-backup-", "sotuhire-data-export-")


class DataArchiveError(ValueError):
    """An invalid or unsafe archive request."""


def data_health() -> DataHealthResponse:
    """Run the storage health scan without exposing filesystem locations."""
    report = check_data_health()
    return DataHealthResponse(
        checked_at=report.checked_at,
        healthy=report.healthy,
        database_present=report.database_path.is_file(),
        schema_version=report.schema_version,
        counts=report.counts,
        issues=[
            DataHealthIssueResponse(
                code=issue.code,
                severity=issue.severity,
                message=issue.message,
                store=_safe_store_label(issue.store),
                record_id=issue.record_id,
            )
            for issue in report.issues
        ],
    )


def list_data_archives() -> DataArchivesResponse:
    """List only valid SotuHire archives from the managed backup directory."""
    root = _archive_directory()
    root.mkdir(parents=True, exist_ok=True)
    archives: list[DataArchiveResponse] = []
    for path in root.glob("sotuhire-data-*.zip"):
        try:
            archives.append(_archive_response(path))
        except (OSError, ValueError, zipfile.BadZipFile):
            # Invalid files are not offered for restore. The restore validator still
            # reports a clear error if a known name is requested directly.
            continue
    archives.sort(key=lambda item: item.created_at, reverse=True)
    return DataArchivesResponse(archives=archives)


def create_data_archive(kind: Literal["backup", "export"]) -> DataArchiveResponse:
    """Create a backup/export at the server-managed destination."""
    if kind not in {"backup", "export"}:
        raise DataArchiveError("Tipo de arquivo de dados inválido.")
    result: BackupResult = create_backup(data_dir=default_data_dir(), kind=kind)
    return _archive_response(result.archive_path, manifest=result.manifest)


def resolve_data_archive(archive_name: str) -> Path:
    """Resolve a client archive identifier without permitting path traversal."""
    if not archive_name.startswith(ARCHIVE_PREFIXES) or not archive_name.endswith(".zip"):
        raise DataArchiveError("Nome de backup inválido.")
    if Path(archive_name).name != archive_name:
        raise DataArchiveError("Caminho de backup inválido.")
    root = _archive_directory().resolve()
    candidate = (root / archive_name).resolve()
    if candidate.parent != root:
        raise DataArchiveError("Backup fora do diretório permitido.")
    if not candidate.is_file():
        raise FileNotFoundError("Backup local não encontrado.")
    return candidate


def restore_data(payload: DataRestoreRequest) -> DataRestoreResponse:
    """Validate an archive, or restore it after explicit human confirmation."""
    archive = resolve_data_archive(payload.archive_name)
    if payload.apply and payload.confirmation != RESTORE_CONFIRMATION:
        raise DataArchiveError(f'Digite "{RESTORE_CONFIRMATION}" para confirmar a restauração.')
    result = restore_backup(
        archive,
        destination=default_data_dir(),
        dry_run=not payload.apply,
    )
    return DataRestoreResponse(
        archive_name=archive.name,
        dry_run=result.dry_run,
        files_validated=result.files_validated,
        files_restored=result.files_restored,
        pre_restore_backup_name=(
            result.pre_restore_backup.name if result.pre_restore_backup is not None else ""
        ),
        warnings=result.warnings,
        message=(
            "Backup validado. Nenhum dado foi alterado."
            if result.dry_run
            else "Restauração concluída após criar um backup de segurança."
        ),
    )


def _archive_directory() -> Path:
    return default_data_dir() / "backups"


def _archive_response(
    archive: Path, *, manifest: BackupManifest | None = None
) -> DataArchiveResponse:
    resolved_manifest = manifest or _read_archive_manifest(archive)
    return DataArchiveResponse(
        archive_name=archive.name,
        kind=resolved_manifest.kind,
        app_version=resolved_manifest.app_version,
        schema_version=resolved_manifest.schema_version,
        created_at=resolved_manifest.created_at,
        size=archive.stat().st_size,
        files_count=len(resolved_manifest.files),
        download_url=f"/api/v1/data/backups/{archive.name}",
    )


def _read_archive_manifest(archive: Path) -> BackupManifest:
    with zipfile.ZipFile(archive) as bundle:
        try:
            content = bundle.read("manifest.json")
        except KeyError as exc:
            raise DataArchiveError("Backup sem manifesto.") from exc
    return BackupManifest.model_validate_json(content)


def _safe_store_label(value: str) -> str:
    """Keep useful relative labels while withholding absolute user paths."""
    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        return path.as_posix()
    data_root = default_data_dir().resolve()
    try:
        return path.resolve().relative_to(data_root).as_posix()
    except ValueError:
        return path.name
