"""API adapter for the professional asset library."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from modules.professional_assets import (
    AssetStatus,
    ProfessionalAsset,
    ProfessionalAssetRepository,
)
from modules.professional_assets.models import utc_now

from apps.api.schemas.professional_assets import (
    ProfessionalAssetPage,
    ProfessionalAssetResponse,
)


class ProfessionalAssetApiService:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.repository = ProfessionalAssetRepository(database_path)

    def save(self, asset: ProfessionalAsset) -> ProfessionalAssetResponse:
        return ProfessionalAssetResponse(asset=self.repository.save(asset))

    def get(self, asset_id: str) -> ProfessionalAssetResponse:
        asset = self.repository.get(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset profissional não encontrado.")
        return ProfessionalAssetResponse(asset=asset)

    def list(
        self,
        *,
        asset_type: str = "",
        session_id: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> ProfessionalAssetPage:
        bounded_limit = max(1, min(limit, 200))
        bounded_offset = max(0, offset)
        return ProfessionalAssetPage(
            items=self.repository.list(
                asset_type=asset_type,
                session_id=session_id,
                limit=bounded_limit,
                offset=bounded_offset,
            ),
            limit=bounded_limit,
            offset=bounded_offset,
        )

    def update(
        self,
        asset_id: str,
        *,
        content: str | None = None,
        title: str | None = None,
    ) -> ProfessionalAssetResponse:
        current = self.get(asset_id).asset
        updated = current.model_copy(
            update={
                "content": current.content if content is None else content,
                "title": current.title if title is None else title,
                "status": AssetStatus.REVIEW,
                "updated_at": utc_now(),
            }
        )
        return self.save(ProfessionalAsset.model_validate(updated.model_dump()))

    def change_status(
        self,
        asset_id: str,
        status: str,
        *,
        content: str | None = None,
    ) -> ProfessionalAssetResponse:
        try:
            resolved = AssetStatus(status)
            changed = self.repository.change_status(asset_id, resolved, content=content)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if changed is None:
            raise HTTPException(status_code=404, detail="Asset profissional não encontrado.")
        return ProfessionalAssetResponse(asset=changed)


def get_professional_asset_api_service() -> ProfessionalAssetApiService:
    return ProfessionalAssetApiService()


__all__ = ["ProfessionalAssetApiService", "get_professional_asset_api_service"]
