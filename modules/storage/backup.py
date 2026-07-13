"""Secret-safe local backup, export and restore operations."""

from __future__ import annotations

import hashlib
import re
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from modules.storage.database import default_data_dir
from modules.storage.migrations import MigrationRunner
from modules.storage.migrations.versions import LATEST_SCHEMA_VERSION

APP_VERSION = "1.9.6"
EXCLUDED_PARTS = {
    "secrets",
    "secret",
    "credentials",
    "tokens",
    "cookies",
    "scraping-cache",
    "backups",
    "__pycache__",
}
EXCLUDED_NAME_MARKERS = ("api-key", "apikey", "credential", "secret", "token", "cookie")
SUPPORTED_SUFFIXES = {
    ".json",
    ".jsonl",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".toml",
    ".yaml",
    ".yml",
}


class BackupFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    size: int
    sha256: str


class BackupManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format_version: str = "1"
    kind: Literal["backup", "export"] = "backup"
    app_version: str = APP_VERSION
    schema_version: int = 0
    max_supported_schema_version: int = LATEST_SCHEMA_VERSION
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    files: list[BackupFile] = Field(default_factory=list)
    excluded_categories: list[str] = Field(
        default_factory=lambda: ["API keys", "tokens", "cookies", "extension storage"]
    )
    excluded_files: list[str] = Field(default_factory=list)


class BackupResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archive_path: Path
    manifest: BackupManifest


class RestoreResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archive_path: Path
    destination: Path
    dry_run: bool
    files_validated: int = 0
    files_restored: int = 0
    pre_restore_backup: Path | None = None
    warnings: list[str] = Field(default_factory=list)


def create_backup(
    *,
    data_dir: str | Path | None = None,
    destination: str | Path | None = None,
    kind: Literal["backup", "export"] = "backup",
) -> BackupResult:
    """Create a portable, checksummed archive without local secrets."""
    source = Path(data_dir) if data_dir is not None else default_data_dir()
    source.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    default_name = (
        f"sotuhire-data-export-{timestamp[:8]}.zip"
        if kind == "export"
        else f"sotuhire-data-backup-{timestamp}.zip"
    )
    archive = Path(destination) if destination is not None else source / "backups" / default_name
    archive.parent.mkdir(parents=True, exist_ok=True)
    database = source / "sotuhire.db"
    schema_version = MigrationRunner(database).current_version() if database.is_file() else 0
    manifest = BackupManifest(kind=kind, schema_version=schema_version)

    with tempfile.TemporaryDirectory(prefix="sotuhire-backup-") as temporary_directory:
        temporary = Path(temporary_directory)
        database_copies: dict[Path, Path] = {}
        for path in sorted(source.rglob("*")):
            if not path.is_file() or path.resolve() == archive.resolve():
                continue
            relative = path.relative_to(source)
            if not _allowed(relative, path):
                manifest.excluded_files.append(relative.as_posix())
                continue
            if _contains_secret_material(path):
                manifest.excluded_files.append(relative.as_posix())
                continue
            safe_source = path
            if path.suffix.casefold() in {".db", ".sqlite", ".sqlite3"}:
                safe_source = temporary / relative
                safe_source.parent.mkdir(parents=True, exist_ok=True)
                _sqlite_backup(path, safe_source)
                database_copies[path] = safe_source
            content_hash = _sha256(safe_source)
            manifest.files.append(
                BackupFile(
                    path=relative.as_posix(), size=safe_source.stat().st_size, sha256=content_hash
                )
            )

        with zipfile.ZipFile(
            archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as bundle:
            for item in manifest.files:
                original = source / Path(item.path)
                source_path = database_copies.get(original, original)
                bundle.write(source_path, item.path)
            bundle.writestr(
                "manifest.json",
                manifest.model_dump_json(indent=2),
            )
    return BackupResult(archive_path=archive, manifest=manifest)


def backup_database_file(database_path: str | Path) -> Path:
    """Create a consistent pre-migration copy of one SQLite database."""
    source = Path(database_path)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    destination = source.parent / "backups" / f"{source.stem}-pre-migration-{timestamp}.db"
    destination.parent.mkdir(parents=True, exist_ok=True)
    _sqlite_backup(source, destination)
    return destination


def restore_backup(
    archive_path: str | Path,
    *,
    destination: str | Path | None = None,
    dry_run: bool = True,
) -> RestoreResult:
    """Validate and optionally restore a backup after creating a safety copy."""
    archive = Path(archive_path)
    target = Path(destination) if destination is not None else default_data_dir()
    if not archive.is_file():
        raise FileNotFoundError(f"Backup não encontrado: {archive}")
    with zipfile.ZipFile(archive) as bundle:
        manifest = _read_manifest(bundle)
        _validate_manifest_compatibility(manifest)
        if manifest.schema_version > LATEST_SCHEMA_VERSION:
            raise ValueError(
                f"Schema {manifest.schema_version} é mais novo que o suportado "
                f"({LATEST_SCHEMA_VERSION})."
            )
        members = {item.filename: item for item in bundle.infolist()}
        declared_paths = [item.path for item in manifest.files]
        if len(declared_paths) != len(set(declared_paths)):
            raise ValueError("Backup contém caminhos duplicados no manifesto.")
        for item in manifest.files:
            _safe_relative_path(item.path)
            if not _allowed(Path(item.path), Path(item.path)):
                raise ValueError(f"Backup contém caminho proibido: {item.path}")
            member = members.get(item.path)
            if member is None:
                raise ValueError(f"Arquivo declarado ausente no backup: {item.path}")
            if member.file_size != item.size:
                raise ValueError(f"Tamanho divergente: {item.path}")
            digest = hashlib.sha256(bundle.read(member)).hexdigest()
            if digest != item.sha256:
                raise ValueError(f"Checksum inválido: {item.path}")
        _validate_sqlite_members(bundle, manifest)

        result = RestoreResult(
            archive_path=archive,
            destination=target,
            dry_run=dry_run,
            files_validated=len(manifest.files),
        )
        if dry_run:
            return result

        if target.exists() and any(target.iterdir()):
            result.pre_restore_backup = create_backup(data_dir=target).archive_path
        with tempfile.TemporaryDirectory(prefix="sotuhire-restore-") as temporary_directory:
            staging = Path(temporary_directory)
            for item in manifest.files:
                destination_path = staging / Path(item.path)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                destination_path.write_bytes(bundle.read(item.path))
            for item in manifest.files:
                source_path = staging / Path(item.path)
                destination_path = target / Path(item.path)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                temporary_path = destination_path.with_suffix(f"{destination_path.suffix}.restore")
                shutil.copy2(source_path, temporary_path)
                temporary_path.replace(destination_path)
                result.files_restored += 1
        return result


def _read_manifest(bundle: zipfile.ZipFile) -> BackupManifest:
    try:
        payload = bundle.read("manifest.json")
    except KeyError as exc:
        raise ValueError("Backup sem manifest.json.") from exc
    return BackupManifest.model_validate_json(payload)


def _validate_manifest_compatibility(manifest: BackupManifest) -> None:
    if manifest.format_version != "1":
        raise ValueError(f"Formato de backup incompatível: {manifest.format_version}")
    current_major = _version_major(APP_VERSION)
    archive_major = _version_major(manifest.app_version)
    if archive_major > current_major:
        raise ValueError(
            f"Backup criado por versão incompatível do aplicativo: {manifest.app_version}"
        )


def _validate_sqlite_members(bundle: zipfile.ZipFile, manifest: BackupManifest) -> None:
    for item in manifest.files:
        if Path(item.path).suffix.casefold() not in {".db", ".sqlite", ".sqlite3"}:
            continue
        with tempfile.TemporaryDirectory(prefix="sotuhire-validate-db-") as directory:
            database = Path(directory) / "archive.db"
            database.write_bytes(bundle.read(item.path))
            try:
                with closing(
                    sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
                ) as connection:
                    integrity = connection.execute("PRAGMA integrity_check").fetchone()
                    if integrity is None or str(integrity[0]).casefold() != "ok":
                        raise ValueError(f"Banco SQLite corrompido no backup: {item.path}")
                    if connection.execute("PRAGMA foreign_key_check").fetchall():
                        raise ValueError(f"Banco SQLite contém referências inválidas: {item.path}")
                    if Path(item.path).name == "sotuhire.db":
                        actual_schema = _archived_schema_version(connection)
                        if actual_schema != manifest.schema_version:
                            raise ValueError(
                                "Schema do banco diverge do manifesto: "
                                f"{actual_schema} != {manifest.schema_version}"
                            )
            except sqlite3.DatabaseError as exc:
                raise ValueError(f"Banco SQLite inválido no backup: {item.path}") from exc


def _archived_schema_version(connection: sqlite3.Connection) -> int:
    history_exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='migration_history'"
    ).fetchone()
    if history_exists is None:
        return 0
    history = connection.execute(
        "SELECT COALESCE(MAX(version), 0) FROM migration_history WHERE success = 1"
    ).fetchone()
    history_version = int(history[0]) if history is not None else 0
    metadata_exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_metadata'"
    ).fetchone()
    if metadata_exists is None:
        raise ValueError("Banco versionado sem schema_metadata.")
    metadata = connection.execute(
        "SELECT value FROM schema_metadata WHERE key='schema_version'"
    ).fetchone()
    try:
        metadata_version = int(metadata[0]) if metadata is not None else -1
    except (TypeError, ValueError):
        metadata_version = -1
    if metadata_version != history_version:
        raise ValueError("Schema divergente dentro do banco arquivado.")
    return history_version


def _version_major(value: str) -> int:
    try:
        return int(value.split(".", 1)[0])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Versão de aplicativo inválida no backup: {value}") from exc


def _safe_relative_path(value: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise ValueError(f"Caminho inseguro no backup: {value}")
    return Path(*pure.parts)


def _allowed(relative: Path, source: Path) -> bool:
    parts = {part.casefold() for part in relative.parts}
    name = relative.name.casefold()
    if parts & EXCLUDED_PARTS:
        return False
    if any(marker in name for marker in EXCLUDED_NAME_MARKERS):
        return False
    if ".local." in name or name.startswith("."):
        return False
    return source.suffix.casefold() in SUPPORTED_SUFFIXES


def _contains_secret_material(path: Path) -> bool:
    """Conservatively reject text stores that appear to contain credentials."""
    if path.suffix.casefold() in {".db", ".sqlite", ".sqlite3"}:
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return True
    if re.search(r"\bAIza[0-9A-Za-z_-]{20,}\b", text):
        return True
    if re.search(r"\bsk-(?:proj-)?[0-9A-Za-z_-]{20,}\b", text):
        return True
    return bool(
        re.search(
            r"(?i)(?:api[_-]?key|authorization|access[_-]?token|refresh[_-]?token)"
            r"\s*[\"']?\s*[:=]\s*[\"']?[^\s\"']{8,}",
            text,
        )
    )


def _sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        closing(sqlite3.connect(source)) as source_connection,
        closing(sqlite3.connect(destination)) as destination_connection,
    ):
        source_connection.backup(destination_connection)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
