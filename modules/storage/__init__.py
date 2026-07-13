"""Local-first persistence, repositories, migrations and immutable snapshots."""

from .ai_runs import AiRun, AiRunStore
from .applications import ApplicationRecord, ApplicationRepository
from .database import connect_database, default_database_path
from .local_store import LocalStore
from .migrations import LATEST_SCHEMA_VERSION, MigrationRunner, ensure_database
from .models import StoredAnalysis
from .snapshots import (
    AnalysisSnapshot,
    JobSnapshot,
    PublicExamSnapshot,
    ResumeSnapshot,
    SnapshotStore,
)

__all__ = [
    "LATEST_SCHEMA_VERSION",
    "AiRun",
    "AiRunStore",
    "AnalysisSnapshot",
    "ApplicationRecord",
    "ApplicationRepository",
    "JobSnapshot",
    "LocalStore",
    "MigrationRunner",
    "PublicExamSnapshot",
    "ResumeSnapshot",
    "SnapshotStore",
    "StoredAnalysis",
    "connect_database",
    "default_database_path",
    "ensure_database",
]
