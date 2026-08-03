from __future__ import annotations

import pytest
from apps.api.main import create_app
from apps.api.services.professional_assets import (
    ProfessionalAssetApiService,
    get_professional_asset_api_service,
)
from fastapi.testclient import TestClient
from modules.professional_assets import (
    AssetStatus,
    AssetType,
    ProfessionalAsset,
    ProfessionalAssetRepository,
)
from modules.storage.database import connect_database
from modules.storage.migrations import ensure_database
from tests.api_test_helpers import api_test_settings, authenticated_test_client


def _asset(*, session_id: str = "") -> ProfessionalAsset:
    return ProfessionalAsset(
        asset_id="asset-fixture",
        asset_type=AssetType.COVER_LETTER,
        title="Carta curta",
        status=AssetStatus.REVIEW,
        content="Experiência confirmada em qualidade.",
        profile_id="profile-asset",
        application_lab_session_id=session_id,
        evidence_scope_id="scope-asset",
        source_refs=["fixture://experience"],
        evidence_ids=["evidence-fixture"],
        document_snapshot_ids=["resume-snapshot-fixture"],
        dependency_hash="a" * 64,
    )


def test_asset_repository_preserves_provenance_and_stales_dependencies(tmp_path) -> None:
    repository = ProfessionalAssetRepository(tmp_path / "sotuhire.db")
    ensure_database(repository.database_path)
    with connect_database(repository.database_path) as connection:
        connection.execute(
            """INSERT INTO application_lab_sessions
            (session_id, job_id, status, created_at, updated_at)
            VALUES ('session-asset', 'job-fixture', 'draft', ?, ?)""",
            ("2026-08-03T00:00:00+00:00", "2026-08-03T00:00:00+00:00"),
        )
    saved = repository.save(_asset(session_id="session-asset"))
    confirmed = repository.change_status(saved.asset_id, AssetStatus.CONFIRMED)

    assert confirmed is not None and confirmed.status is AssetStatus.CONFIRMED
    assert confirmed.source_refs == ["fixture://experience"]
    assert confirmed.review_status == "confirmed"
    assert repository.mark_session_stale("session-asset", "job_changed") == 1
    stale = repository.get(saved.asset_id)
    assert stale is not None and stale.status is AssetStatus.STALE
    assert stale.stale_reason == "job_changed"

    with pytest.raises(ValueError, match="evidência"):
        ProfessionalAsset(
            asset_type=AssetType.RECRUITER_MESSAGE,
            status=AssetStatus.CONFIRMED,
            content="Afirmação sem fonte.",
            dependency_hash="b" * 64,
        )


def test_professional_asset_api_review_confirm_archive_and_undo(tmp_path) -> None:
    service = ProfessionalAssetApiService(tmp_path / "sotuhire.db")
    app = create_app(api_test_settings())
    app.dependency_overrides[get_professional_asset_api_service] = lambda: service
    client: TestClient = authenticated_test_client(app)

    created = client.post(
        "/api/v1/professional-assets",
        json={"asset": _asset().model_dump(mode="json")},
    )
    edited = client.patch(
        "/api/v1/professional-assets/asset-fixture",
        json={"content": "Experiência confirmada e revisada."},
    )
    confirmed = client.post(
        "/api/v1/professional-assets/asset-fixture/status",
        json={"status": "confirmed"},
    )
    archived = client.post(
        "/api/v1/professional-assets/asset-fixture/status",
        json={"status": "archived"},
    )
    undone = client.post(
        "/api/v1/professional-assets/asset-fixture/status",
        json={"status": "draft"},
    )

    assert created.status_code == edited.status_code == confirmed.status_code == 200
    assert edited.json()["data"]["asset"]["source_refs"] == ["fixture://experience"]
    assert confirmed.json()["data"]["asset"]["status"] == "confirmed"
    assert archived.json()["data"]["asset"]["status"] == "archived"
    assert undone.json()["data"]["asset"]["status"] == "draft"
    assert client.get("/api/v1/professional-assets").json()["data"]["items"]
