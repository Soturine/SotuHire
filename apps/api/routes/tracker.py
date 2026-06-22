"""Tracker and Application Intelligence endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from apps.api.routes.responses import ok
from apps.api.schemas.analysis import (
    TrackerFunnelResponse,
    TrackerJobCreateRequest,
    TrackerJobResponse,
    TrackerJobsResponse,
    TrackerJobUpdateRequest,
    TrackerMetricsResponse,
    TrackerRequirementsResponse,
    TrackerSourcesResponse,
)
from apps.api.schemas.common import ApiEnvelope
from apps.api.services.tracker import TrackerService, get_tracker_service

router = APIRouter(prefix="/api/v1/tracker", tags=["tracker"])
TrackerDependency = Annotated[TrackerService, Depends(get_tracker_service)]


@router.get("/jobs", response_model=ApiEnvelope[TrackerJobsResponse])
def tracker_jobs(
    service: TrackerDependency,
) -> ApiEnvelope[TrackerJobsResponse]:
    """List local tracker jobs."""
    return ok(service.list_jobs())


@router.post("/jobs", response_model=ApiEnvelope[TrackerJobResponse])
def tracker_create_job(
    payload: TrackerJobCreateRequest,
    service: TrackerDependency,
) -> ApiEnvelope[TrackerJobResponse]:
    """Create or upsert a tracker job."""
    return ok(service.create_job(payload), request_id=payload.request_id)


@router.patch("/jobs/{record_id}", response_model=ApiEnvelope[TrackerJobResponse])
def tracker_update_job(
    record_id: str,
    payload: TrackerJobUpdateRequest,
    service: TrackerDependency,
) -> ApiEnvelope[TrackerJobResponse]:
    """Update a tracker job."""
    return ok(
        service.update_job(record_id, status=payload.status, notes=payload.notes),
        request_id=payload.request_id,
    )


@router.get("/metrics", response_model=ApiEnvelope[TrackerMetricsResponse])
def tracker_metrics(
    service: TrackerDependency,
) -> ApiEnvelope[TrackerMetricsResponse]:
    """Return tracker KPI metrics."""
    return ok(service.metrics())


@router.get("/requirements", response_model=ApiEnvelope[TrackerRequirementsResponse])
def tracker_requirements(
    service: TrackerDependency,
) -> ApiEnvelope[TrackerRequirementsResponse]:
    """Return requirement and gap rankings."""
    return ok(service.requirements())


@router.get("/funnel", response_model=ApiEnvelope[TrackerFunnelResponse])
def tracker_funnel(
    service: TrackerDependency,
) -> ApiEnvelope[TrackerFunnelResponse]:
    """Return application funnel metrics."""
    return ok(service.funnel())


@router.get("/sources", response_model=ApiEnvelope[TrackerSourcesResponse])
def tracker_sources(
    service: TrackerDependency,
) -> ApiEnvelope[TrackerSourcesResponse]:
    """Return source performance metrics."""
    return ok(service.sources())
