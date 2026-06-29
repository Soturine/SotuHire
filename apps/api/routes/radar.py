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
    RadarScheduledRunResponse,
    RadarScheduledRunsResponse,
    RadarSchedulePatchRequest,
    RadarScheduleRequest,
    RadarScheduleResponse,
    RadarSchedulerStatusResponse,
    RadarSchedulesResponse,
    RadarSourcePatchRequest,
    RadarSourceRequest,
    RadarSourceResponse,
    RadarSourcesResponse,
    RadarStatsResponse,
    RadarWishlistDraftRequest,
    RadarWishlistDraftResponse,
    RadarWishlistPatchRequest,
    RadarWishlistRequest,
    RadarWishlistResponse,
    RadarWishlistsResponse,
)
from apps.api.services.radar import (
    radar_alerts,
    radar_create_schedule,
    radar_create_source,
    radar_create_wishlist,
    radar_delete_schedule,
    radar_delete_source,
    radar_delete_wishlist,
    radar_draft_wishlist,
    radar_get_schedule,
    radar_patch_alert,
    radar_patch_result,
    radar_patch_schedule,
    radar_patch_source,
    radar_patch_wishlist,
    radar_results,
    radar_run,
    radar_run_schedule_now,
    radar_runs,
    radar_save_inbox,
    radar_save_tracker,
    radar_scheduled_runs,
    radar_scheduler_start,
    radar_scheduler_status,
    radar_scheduler_stop,
    radar_schedules,
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


@router.post("/wishlists/draft", response_model=ApiEnvelope[RadarWishlistDraftResponse])
def draft_wishlist(
    payload: RadarWishlistDraftRequest,
) -> ApiEnvelope[RadarWishlistDraftResponse]:
    """Create an unsaved AI/local wishlist draft from free text."""
    data, warnings = radar_draft_wishlist(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


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


@router.get("/schedules", response_model=ApiEnvelope[RadarSchedulesResponse])
def schedules() -> ApiEnvelope[RadarSchedulesResponse]:
    """List local Radar schedules."""
    return ok(radar_schedules())


@router.post("/schedules", response_model=ApiEnvelope[RadarScheduleResponse])
def create_schedule(payload: RadarScheduleRequest) -> ApiEnvelope[RadarScheduleResponse]:
    """Create one local Radar schedule."""
    return ok(radar_create_schedule(payload), request_id=payload.request_id)


@router.get("/schedules/{schedule_id}", response_model=ApiEnvelope[RadarScheduleResponse])
def get_schedule(schedule_id: str) -> ApiEnvelope[RadarScheduleResponse]:
    """Return one local Radar schedule."""
    return ok(radar_get_schedule(schedule_id))


@router.patch("/schedules/{schedule_id}", response_model=ApiEnvelope[RadarScheduleResponse])
def patch_schedule(
    schedule_id: str,
    payload: RadarSchedulePatchRequest,
) -> ApiEnvelope[RadarScheduleResponse]:
    """Patch one local Radar schedule."""
    return ok(radar_patch_schedule(schedule_id, payload), request_id=payload.request_id)


@router.delete("/schedules/{schedule_id}", response_model=ApiEnvelope[RadarScheduleResponse])
def delete_schedule(schedule_id: str) -> ApiEnvelope[RadarScheduleResponse]:
    """Disable one local Radar schedule."""
    return ok(radar_delete_schedule(schedule_id))


@router.post(
    "/schedules/{schedule_id}/run-now",
    response_model=ApiEnvelope[RadarScheduledRunResponse],
)
def run_schedule_now(schedule_id: str) -> ApiEnvelope[RadarScheduledRunResponse]:
    """Run one schedule immediately for manual review."""
    return ok(radar_run_schedule_now(schedule_id))


@router.get("/scheduled-runs", response_model=ApiEnvelope[RadarScheduledRunsResponse])
def scheduled_runs() -> ApiEnvelope[RadarScheduledRunsResponse]:
    """List scheduled Radar run history."""
    return ok(radar_scheduled_runs())


@router.get("/scheduler/status", response_model=ApiEnvelope[RadarSchedulerStatusResponse])
def scheduler_status() -> ApiEnvelope[RadarSchedulerStatusResponse]:
    """Return local scheduler status."""
    return ok(radar_scheduler_status())


@router.post("/scheduler/start", response_model=ApiEnvelope[RadarSchedulerStatusResponse])
def scheduler_start() -> ApiEnvelope[RadarSchedulerStatusResponse]:
    """Start the in-process local scheduler."""
    return ok(radar_scheduler_start())


@router.post("/scheduler/stop", response_model=ApiEnvelope[RadarSchedulerStatusResponse])
def scheduler_stop() -> ApiEnvelope[RadarSchedulerStatusResponse]:
    """Stop the in-process local scheduler."""
    return ok(radar_scheduler_stop())


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
