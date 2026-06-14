"""Local Companion API for assistive browser captures."""

from modules.core.collection_method import CollectionMethod

from .app import CompanionCaptureStore, LocalCompanionApp, LocalCompanionService
from .schemas import (
    ApplicationBatchPayload,
    BrowserCapturePayload,
    CaptureActionRequest,
    CompanionAnalysisContext,
    CompanionCaptureRecord,
    CompanionResponse,
)
from .server import server_status, start_server, stop_server

__all__ = [
    "BrowserCapturePayload",
    "CollectionMethod",
    "ApplicationBatchPayload",
    "CaptureActionRequest",
    "CompanionAnalysisContext",
    "CompanionCaptureRecord",
    "CompanionCaptureStore",
    "CompanionResponse",
    "LocalCompanionApp",
    "LocalCompanionService",
    "server_status",
    "start_server",
    "stop_server",
]
