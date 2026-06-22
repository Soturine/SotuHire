"""Source collection endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from modules.scraping.browser_session import DEFAULT_CDP_URL

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.sources import (
    AuthenticatedBrowserCollectRequest,
    AuthenticatedBrowserCollectResponse,
    AuthenticatedBrowserLaunchRequest,
    AuthenticatedBrowserStatusResponse,
)
from apps.api.services.sources import (
    authenticated_browser_collect,
    authenticated_browser_launch,
    authenticated_browser_status,
)

router = APIRouter(prefix="/api/v1/sources/authenticated-browser", tags=["sources"])


@router.get("/status", response_model=ApiEnvelope[AuthenticatedBrowserStatusResponse])
def browser_status(
    browser_cdp_url: str = DEFAULT_CDP_URL,
) -> ApiEnvelope[AuthenticatedBrowserStatusResponse]:
    """Inspect the local CDP browser session."""
    return ok(authenticated_browser_status(browser_cdp_url))


@router.post("/launch", response_model=ApiEnvelope[AuthenticatedBrowserStatusResponse])
def browser_launch(
    payload: AuthenticatedBrowserLaunchRequest,
) -> ApiEnvelope[AuthenticatedBrowserStatusResponse]:
    """Open the dedicated browser so the user can log in manually."""
    return ok(authenticated_browser_launch(payload), request_id=payload.request_id)


@router.post("/collect", response_model=ApiEnvelope[AuthenticatedBrowserCollectResponse])
def browser_collect(
    payload: AuthenticatedBrowserCollectRequest,
) -> ApiEnvelope[AuthenticatedBrowserCollectResponse]:
    """Collect opportunities from an authorized authenticated browser session."""
    return ok(authenticated_browser_collect(payload), request_id=payload.request_id)
