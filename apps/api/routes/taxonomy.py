"""Versioned taxonomy dataset and human-review endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from modules.storage.career_intelligence import CareerIntelligenceRepository
from modules.storage.database import default_data_dir
from modules.taxonomy import (
    TaxonomyDatasetManifest,
    TaxonomyMapping,
    VersionedTaxonomyStore,
)
from pydantic import BaseModel, ConfigDict, Field

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope

router = APIRouter(prefix="/api/v1/taxonomy", tags=["taxonomy"])


class TaxonomyDatasetImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: TaxonomyDatasetManifest
    records: list[dict[str, object]] = Field(max_length=100_000)


class TaxonomyReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: Literal["confirmed", "rejected"]


@router.post(
    "/datasets",
    response_model=ApiEnvelope[TaxonomyDatasetManifest],
    status_code=201,
)
def import_dataset(
    payload: TaxonomyDatasetImportRequest,
) -> ApiEnvelope[TaxonomyDatasetManifest]:
    store = VersionedTaxonomyStore(default_data_dir() / "taxonomies")
    try:
        store.save(payload.manifest, payload.records)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return ok(CareerIntelligenceRepository().save_dataset(payload.manifest))


@router.get("/datasets", response_model=ApiEnvelope[list[TaxonomyDatasetManifest]])
def list_datasets(
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiEnvelope[list[TaxonomyDatasetManifest]]:
    return ok(CareerIntelligenceRepository().list_datasets(limit=limit))


@router.post(
    "/mappings",
    response_model=ApiEnvelope[TaxonomyMapping],
    status_code=201,
)
def save_mapping(payload: TaxonomyMapping) -> ApiEnvelope[TaxonomyMapping]:
    return ok(CareerIntelligenceRepository().save_mapping(payload))


@router.get("/mappings", response_model=ApiEnvelope[list[TaxonomyMapping]])
def list_mappings(
    review_status: Literal["candidate", "confirmed", "rejected"] | None = None,
    limit: int = Query(default=200, ge=1, le=1_000),
) -> ApiEnvelope[list[TaxonomyMapping]]:
    return ok(
        CareerIntelligenceRepository().list_mappings(review_status=review_status or "", limit=limit)
    )


@router.patch(
    "/mappings/{mapping_id}/review",
    response_model=ApiEnvelope[TaxonomyMapping],
)
def review_mapping(
    mapping_id: str,
    payload: TaxonomyReviewRequest,
) -> ApiEnvelope[TaxonomyMapping]:
    repository = CareerIntelligenceRepository()
    mapping = repository.get_mapping(mapping_id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="Mapeamento nao encontrado.")
    reviewed = mapping.model_copy(
        update={"review_status": payload.review_status, "reviewed_at": datetime.now(UTC)}
    )
    return ok(repository.save_mapping(TaxonomyMapping.model_validate(reviewed)))


__all__ = ["router"]
