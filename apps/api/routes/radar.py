"""Job Radar endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.radar import (
    RadarAlertPatchRequest,
    RadarAlertResponse,
    RadarAlertsResponse,
    RadarResultPatchRequest,
    RadarResultResponse,
    RadarResultsResponse,
    RadarRunRequest,
    RadarRunResponse,
    RadarRunsResponse,
    RadarSaveInboxResponse,
    RadarSaveTrackerResponse,
    RadarSourcePatchRequest,
    RadarSourceRequest,
    RadarSourceResponse,
    RadarSourcesResponse,
    RadarStatsResponse,
    RadarWishlistPatchRequest,
    RadarWishlistRequest,
    RadarWishlistResponse,
    RadarWishlistsResponse,
)
from apps.api.services.radar import (
    radar_alerts,
    radar_create_source,
    radar_create_wishlist,
    radar_delete_source,
    radar_delete_wishlist,
    radar_patch_alert,
    radar_patch_result,
    radar_patch_source,
    radar_patch_wishlist,
    radar_results,
    radar_run,
    radar_runs,
    radar_save_inbox,
    radar_save_tracker,
    radar_sources,
    radar_stats,
    radar_wishlists,
)

router = APIRouter(prefix="/api/v1/radar", tags=["radar"])


@router.get("/wishlists", response_model=ApiEnvelope[RadarWishlistsResponse])
def wishlists() -> ApiEnvelope[RadarWishlistsResponse]:
    """List local radar wishlists."""
    return ok(radar_wishlists())


@router.post("/wishlists", response_model=ApiEnvelope[RadarWishlistResponse])
def create_wishlist(payload: RadarWishlistRequest) -> ApiEnvelope[RadarWishlistResponse]:
    """Create a local radar wishlist."""
    return ok(radar_create_wishlist(payload), request_id=payload.request_id)


@router.patch("/wishlists/{wishlist_id}", response_model=ApiEnvelope[RadarWishlistResponse])
def patch_wishlist(
    wishlist_id: str,
    payload: RadarWishlistPatchRequest,
) -> ApiEnvelope[RadarWishlistResponse]:
    """Patch one radar wishlist."""
    return ok(radar_patch_wishlist(wishlist_id, payload), request_id=payload.request_id)


@router.delete("/wishlists/{wishlist_id}", response_model=ApiEnvelope[RadarWishlistResponse])
def delete_wishlist(wishlist_id: str) -> ApiEnvelope[RadarWishlistResponse]:
    """Deactivate one radar wishlist."""
    return ok(radar_delete_wishlist(wishlist_id))


@router.get("/sources", response_model=ApiEnvelope[RadarSourcesResponse])
def sources() -> ApiEnvelope[RadarSourcesResponse]:
    """List local radar sources."""
    return ok(radar_sources())


@router.post("/sources", response_model=ApiEnvelope[RadarSourceResponse])
def create_source(payload: RadarSourceRequest) -> ApiEnvelope[RadarSourceResponse]:
    """Create one radar source."""
    return ok(radar_create_source(payload), request_id=payload.request_id)


@router.patch("/sources/{source_id}", response_model=ApiEnvelope[RadarSourceResponse])
def patch_source(
    source_id: str,
    payload: RadarSourcePatchRequest,
) -> ApiEnvelope[RadarSourceResponse]:
    """Patch one radar source."""
    return ok(radar_patch_source(source_id, payload), request_id=payload.request_id)


@router.delete("/sources/{source_id}", response_model=ApiEnvelope[RadarSourceResponse])
def delete_source(source_id: str) -> ApiEnvelope[RadarSourceResponse]:
    """Disable one radar source."""
    return ok(radar_delete_source(source_id))


@router.post("/run", response_model=ApiEnvelope[RadarRunResponse])
def run(payload: RadarRunRequest) -> ApiEnvelope[RadarRunResponse]:
    """Execute a manual bounded radar run."""
    data, warnings = radar_run(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.get("/runs", response_model=ApiEnvelope[RadarRunsResponse])
def runs() -> ApiEnvelope[RadarRunsResponse]:
    """List radar run history."""
    return ok(radar_runs())


@router.get("/results", response_model=ApiEnvelope[RadarResultsResponse])
def results(status: str = "", source_id: str = "") -> ApiEnvelope[RadarResultsResponse]:
    """List radar results."""
    return ok(radar_results(status=status, source_id=source_id))


@router.patch("/results/{result_id}", response_model=ApiEnvelope[RadarResultResponse])
def patch_result(
    result_id: str,
    payload: RadarResultPatchRequest,
) -> ApiEnvelope[RadarResultResponse]:
    """Patch one radar result."""
    return ok(radar_patch_result(result_id, payload), request_id=payload.request_id)


@router.post("/results/{result_id}/save-inbox", response_model=ApiEnvelope[RadarSaveInboxResponse])
def save_inbox(result_id: str) -> ApiEnvelope[RadarSaveInboxResponse]:
    """Save one radar result to the opportunity inbox."""
    return ok(radar_save_inbox(result_id))


@router.post(
    "/results/{result_id}/save-tracker",
    response_model=ApiEnvelope[RadarSaveTrackerResponse],
)
def save_tracker(result_id: str) -> ApiEnvelope[RadarSaveTrackerResponse]:
    """Save one radar result to tracker."""
    return ok(radar_save_tracker(result_id))


@router.get("/alerts", response_model=ApiEnvelope[RadarAlertsResponse])
def alerts(unread_only: bool = False) -> ApiEnvelope[RadarAlertsResponse]:
    """List local radar alerts."""
    return ok(radar_alerts(unread_only=unread_only))


@router.patch("/alerts/{alert_id}", response_model=ApiEnvelope[RadarAlertResponse])
def patch_alert(
    alert_id: str,
    payload: RadarAlertPatchRequest,
) -> ApiEnvelope[RadarAlertResponse]:
    """Patch one radar alert."""
    return ok(radar_patch_alert(alert_id, payload), request_id=payload.request_id)


@router.get("/stats", response_model=ApiEnvelope[RadarStatsResponse])
def stats() -> ApiEnvelope[RadarStatsResponse]:
    """Return radar dashboard stats."""
    return ok(radar_stats())
