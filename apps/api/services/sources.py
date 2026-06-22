"""Source collection service adapters for frontend API routes."""

from __future__ import annotations

from fastapi import HTTPException
from modules.scraping.browser_session import inspect_browser_session, launch_authenticated_browser
from modules.scraping.collection import collect_authenticated_source
from modules.scraping.schemas import ScrapingSource

from apps.api.schemas.sources import (
    AuthenticatedBrowserCollectRequest,
    AuthenticatedBrowserCollectResponse,
    AuthenticatedBrowserLaunchRequest,
    AuthenticatedBrowserOpportunityItem,
    AuthenticatedBrowserStatusResponse,
)


def authenticated_browser_status(endpoint: str) -> AuthenticatedBrowserStatusResponse:
    """Return the status of the local authenticated browser session."""
    status = inspect_browser_session(endpoint)
    return AuthenticatedBrowserStatusResponse(
        available=status.available,
        endpoint=status.endpoint,
        browser=status.browser,
        message=status.message,
    )


def authenticated_browser_launch(
    request: AuthenticatedBrowserLaunchRequest,
) -> AuthenticatedBrowserStatusResponse:
    """Open or reuse the dedicated browser for manual login."""
    try:
        status = launch_authenticated_browser(request.start_url, request.browser_cdp_url)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AuthenticatedBrowserStatusResponse(
        available=status.available,
        endpoint=status.endpoint,
        browser=status.browser,
        message=status.message,
    )


def authenticated_browser_collect(
    request: AuthenticatedBrowserCollectRequest,
) -> AuthenticatedBrowserCollectResponse:
    """Collect opportunities through the existing authorized browser connector."""
    if not request.authorized_use:
        raise HTTPException(
            status_code=422,
            detail="Confirme que o uso da fonte autenticada esta autorizado antes de coletar.",
        )

    source = ScrapingSource(
        name=request.name,
        type="authenticated_browser",
        url=request.url,
        collection_mode="AUTHENTICATED_BROWSER",
        enabled=True,
        max_items=request.max_items,
        max_pages=request.max_pages,
        delay_seconds=request.delay_seconds,
        browser_cdp_url=request.browser_cdp_url,
        authorized_use=request.authorized_use,
        authorization_reference=request.authorization_reference,
    )
    result = collect_authenticated_source(source)
    return AuthenticatedBrowserCollectResponse(
        new_count=result.new_count,
        duplicate_count=result.duplicate_count,
        updated_count=result.updated_count,
        failures=result.failures,
        opportunities=[
            AuthenticatedBrowserOpportunityItem(
                title=opportunity.title,
                company=opportunity.company or "",
                source_url=opportunity.source_url,
                confidence=opportunity.confidence,
            )
            for opportunity in result.opportunities
        ],
    )
