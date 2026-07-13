"""Contracts for local data health, backup, export and restore operations."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DataHealthIssueResponse(BaseModel):
    """One actionable finding from the read-only data health scan."""

    model_config = ConfigDict(extra="forbid")

    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    store: str = ""
    record_id: str = ""


class DataHealthResponse(BaseModel):
    """Secret-safe data health summary for the local frontend."""

    model_config = ConfigDict(extra="forbid")

    checked_at: datetime
    healthy: bool
    database_present: bool
    schema_version: int
    counts: dict[str, int] = Field(default_factory=dict)
    issues: list[DataHealthIssueResponse] = Field(default_factory=list)


class DataArchiveResponse(BaseModel):
    """Public metadata for an archive kept in the local backup directory."""

    model_config = ConfigDict(extra="forbid")

    archive_name: str
    kind: Literal["backup", "export"]
    app_version: str
    schema_version: int
    created_at: datetime
    size: int
    files_count: int
    download_url: str


class DataArchivesResponse(BaseModel):
    """Archives available to download or restore locally."""

    model_config = ConfigDict(extra="forbid")

    archives: list[DataArchiveResponse] = Field(default_factory=list)


class DataBackupCreateRequest(BaseModel):
    """Request a backup or a portable export at the server-managed location."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["backup", "export"] = "backup"


class DataRestoreRequest(BaseModel):
    """Validate by default; applying requires an explicit confirmation phrase."""

    model_config = ConfigDict(extra="forbid")

    archive_name: str = Field(
        min_length=1,
        max_length=180,
        pattern=r"^sotuhire-data-(?:backup|export)-[A-Za-z0-9._-]+\.zip$",
    )
    apply: bool = False
    confirmation: str = Field(default="", max_length=32)


class DataRestoreResponse(BaseModel):
    """Validation or restore result without exposing local absolute paths."""

    model_config = ConfigDict(extra="forbid")

    archive_name: str
    dry_run: bool
    files_validated: int
    files_restored: int
    pre_restore_backup_name: str = ""
    warnings: list[str] = Field(default_factory=list)
    message: str
