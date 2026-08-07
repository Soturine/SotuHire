"""Recoverable JSON/JSONL persistence with explicit degraded state."""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class JsonStoreError(RuntimeError):
    """Base error for a JSON store that cannot safely continue."""


class JsonStoreCorruptionError(JsonStoreError):
    """Raised after invalid data has been quarantined."""

    def __init__(self, path: Path, quarantine_path: Path | None) -> None:
        self.path = path
        self.quarantine_path = quarantine_path
        super().__init__(f"Store JSON corrompido e bloqueado: {path}")


class JsonStoreWriteBlockedError(JsonStoreError):
    """Raised when degraded data would otherwise be overwritten."""


class JsonStoreHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    status: str
    degraded_at: str = ""
    error_type: str = ""
    quarantine_path: str = ""
    backups: list[str] = Field(default_factory=list)


def load_json(
    path: str | Path,
    *,
    validator: Callable[[Any], T],
    default_factory: Callable[[], T],
) -> T:
    target = Path(path)
    _raise_if_degraded(target)
    if not target.exists():
        return default_factory()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        return validator(payload)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise _quarantine(target, exc) from exc


def load_jsonl(
    path: str | Path,
    *,
    validator: Callable[[Any], T],
) -> list[T]:
    target = Path(path)
    _raise_if_degraded(target)
    if not target.exists():
        return []
    try:
        records: list[T] = []
        for line_number, line in enumerate(
            target.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                records.append(validator(json.loads(line)))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Linha JSONL inválida: {line_number}") from exc
        return records
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise _quarantine(target, exc) from exc


def atomic_write_json(path: str | Path, payload: object, *, backups: int = 3) -> Path:
    return atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        backups=backups,
    )


def atomic_write_jsonl(path: str | Path, payloads: Sequence[object], *, backups: int = 3) -> Path:
    content = "\n".join(json.dumps(item, ensure_ascii=False, default=str) for item in payloads)
    return atomic_write_text(path, content + ("\n" if content else ""), backups=backups)


def atomic_write_text(
    path: str | Path,
    content: str,
    *,
    backups: int = 3,
    allow_degraded: bool = False,
) -> Path:
    target = Path(path)
    if not allow_degraded:
        _raise_if_degraded(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        _create_backup(target, keep=max(1, backups))
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def json_store_health(path: str | Path) -> JsonStoreHealth:
    target = Path(path)
    marker = _marker_path(target)
    metadata: dict[str, Any] = {}
    if marker.exists():
        try:
            loaded = json.loads(marker.read_text(encoding="utf-8"))
            metadata = loaded if isinstance(loaded, dict) else {}
        except (OSError, ValueError):
            metadata = {"error_type": "UnreadableDegradedMarker"}
    return JsonStoreHealth(
        path=str(target),
        status="degraded" if marker.exists() else "healthy",
        degraded_at=str(metadata.get("degraded_at", "")),
        error_type=str(metadata.get("error_type", "")),
        quarantine_path=str(metadata.get("quarantine_path", "")),
        backups=[str(item) for item in _backup_files(target)],
    )


def restore_json_store(
    path: str | Path,
    source: str | Path,
    *,
    json_lines: bool = False,
) -> Path:
    """Explicitly restore a valid backup and clear the degraded marker."""
    target = Path(path)
    source_path = Path(source)
    content = source_path.read_text(encoding="utf-8")
    if json_lines:
        for line in content.splitlines():
            if line.strip():
                json.loads(line)
    else:
        json.loads(content)
    atomic_write_text(target, content, allow_degraded=True)
    _marker_path(target).unlink(missing_ok=True)
    return target


def _quarantine(path: Path, error: BaseException) -> JsonStoreCorruptionError:
    quarantine_path: Path | None = None
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        quarantine_dir = path.parent / ".quarantine"
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        quarantine_path = quarantine_dir / (f"{path.name}.{_timestamp()}.{uuid4().hex}.corrupt")
        try:
            os.replace(path, quarantine_path)
        except OSError:
            quarantine_path = None
    marker_payload = {
        "status": "degraded",
        "degraded_at": datetime.now(UTC).isoformat(),
        "error_type": type(error).__name__,
        "quarantine_path": str(quarantine_path or ""),
    }
    _write_marker(_marker_path(path), marker_payload)
    return JsonStoreCorruptionError(path, quarantine_path)


def _raise_if_degraded(path: Path) -> None:
    if _marker_path(path).exists():
        raise JsonStoreWriteBlockedError(
            f"Store em estado degraded; execute restore explícito antes de gravar: {path}"
        )


def _marker_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.degraded.json")


def _create_backup(path: Path, *, keep: int) -> None:
    backup_dir = path.parent / ".backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    destination = backup_dir / f"{path.name}.{_timestamp()}.{uuid4().hex}.bak"
    shutil.copy2(path, destination)
    for expired in _backup_files(path)[keep:]:
        expired.unlink(missing_ok=True)


def _backup_files(path: Path) -> list[Path]:
    backup_dir = path.parent / ".backups"
    if not backup_dir.exists():
        return []
    return sorted(backup_dir.glob(f"{path.name}.*.bak"), reverse=True)


def _write_marker(path: Path, payload: dict[str, str]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


__all__ = [
    "JsonStoreCorruptionError",
    "JsonStoreError",
    "JsonStoreHealth",
    "JsonStoreWriteBlockedError",
    "atomic_write_json",
    "atomic_write_jsonl",
    "atomic_write_text",
    "json_store_health",
    "load_json",
    "load_jsonl",
    "restore_json_store",
]
