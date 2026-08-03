"""Professional asset library endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.professional_assets import (
    ProfessionalAssetCreateRequest,
    ProfessionalAssetPage,
    ProfessionalAssetResponse,
    ProfessionalAssetStatusRequest,
    ProfessionalAssetUpdateRequest,
)
from apps.api.services.professional_assets import (
    ProfessionalAssetApiService,
    get_professional_asset_api_service,
)

router = APIRouter(prefix="/api/v1/professional-assets", tags=["professional-assets"])
AssetDependency = Annotated[
    ProfessionalAssetApiService,
    Depends(get_professional_asset_api_service),
]


@router.post("", response_model=ApiEnvelope[ProfessionalAssetResponse])
def create_asset(
    payload: ProfessionalAssetCreateRequest,
    service: AssetDependency,
) -> ApiEnvelope[ProfessionalAssetResponse]:
    return ok(service.save(payload.asset), request_id=payload.request_id)


@router.get("", response_model=ApiEnvelope[ProfessionalAssetPage])
def list_assets(
    service: AssetDependency,
    asset_type: str = "",
    session_id: str = "",
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ApiEnvelope[ProfessionalAssetPage]:
    return ok(
        service.list(
            asset_type=asset_type,
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/{asset_id}", response_model=ApiEnvelope[ProfessionalAssetResponse])
def get_asset(asset_id: str, service: AssetDependency) -> ApiEnvelope[ProfessionalAssetResponse]:
    return ok(service.get(asset_id))


@router.patch("/{asset_id}", response_model=ApiEnvelope[ProfessionalAssetResponse])
def update_asset(
    asset_id: str,
    payload: ProfessionalAssetUpdateRequest,
    service: AssetDependency,
) -> ApiEnvelope[ProfessionalAssetResponse]:
    return ok(
        service.update(asset_id, content=payload.content, title=payload.title),
        request_id=payload.request_id,
    )


@router.post("/{asset_id}/status", response_model=ApiEnvelope[ProfessionalAssetResponse])
def change_asset_status(
    asset_id: str,
    payload: ProfessionalAssetStatusRequest,
    service: AssetDependency,
) -> ApiEnvelope[ProfessionalAssetResponse]:
    return ok(
        service.change_status(asset_id, payload.status, content=payload.content),
        request_id=payload.request_id,
    )


__all__ = ["router"]
