"""Local Companion API for assistive browser captures."""

from modules.core.collection_method import CollectionMethod

from .app import CompanionCaptureStore, LocalCompanionApp, LocalCompanionService
from .schemas import (
    ApplicationBatchPayload,
    BrowserCapturePayload,
    CaptureActionRequest,
    CompanionAnalysisContext,
    CompanionCaptureRecord,
    CompanionContextSummaryResponse,
    CompanionResponse,
    ProjectCompanionResponse,
)
from .server import server_status, start_server, stop_server

__all__ = [
    "BrowserCapturePayload",
    "CollectionMethod",
    "ApplicationBatchPayload",
    "CaptureActionRequest",
    "CompanionAnalysisContext",
    "CompanionContextSummaryResponse",
    "CompanionCaptureRecord",
    "CompanionCaptureStore",
    "CompanionResponse",
    "ProjectCompanionResponse",
    "LocalCompanionApp",
    "LocalCompanionService",
    "server_status",
    "start_server",
    "stop_server",
]
