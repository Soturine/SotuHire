"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from apps.api.config import ApiSettings
from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope, HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=ApiEnvelope[HealthResponse])
def health(request: Request) -> ApiEnvelope[HealthResponse]:
    """Return local API health and capability metadata."""
    settings: ApiSettings = request.app.state.settings
    return ok(
        HealthResponse(
            version=settings.version,
            capabilities=[
                "resume_extract",
                "job_extract",
                "match_analyze",
                "ats_analyze",
                "resume_tailor",
                "github_repo_analyze",
                "tracker_jobs",
                "application_intelligence",
                "ai_settings",
                "authenticated_browser_sources",
            ],
            cors_allowed_origins=settings.allowed_origins,
        )
    )
