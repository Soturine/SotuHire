from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from apps.api.main import app
from modules.radar import RadarSchedule, RadarScheduleStore, ScheduledRadarService
from modules.radar.models import utc_now
from modules.scraping.schemas import FetchResult
from tests.api_test_helpers import api_client

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Feed ficticio</title>
    <item>
      <title>Estagio Engenharia Qualidade</title>
      <link>https://example.com/jobs/scheduled-1</link>
      <description>Empresa: Empresa Exemplo. Localizacao: Remoto. Requisitos: Excel, qualidade, relatorios tecnicos e NR10.</description>
    </item>
  </channel>
</rss>
"""


def _fake_fetch(self, url: str, *, delay_seconds: float = 0.2) -> FetchResult:
    return FetchResult(
        url=url,
        status_code=200,
        content_type="application/rss+xml",
        text=RSS_XML,
    )


def _create_wishlist(client, name: str = "Engenharia multi area") -> str:
    response = client.post(
        "/api/v1/radar/wishlists",
        json={
            "name": name,
            "target_titles": ["Estagio Engenharia", "Tecnico Industrial"],
            "target_domains": ["Engenharia"],
            "required_skills": ["Excel", "qualidade", "NR10"],
            "desired_skills": ["relatorios tecnicos"],
            "locations": ["Remoto"],
            "remote_preferences": ["remoto"],
            "min_match_score": 60,
            "min_ats_score": 30,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["wishlist"]["id"]


def _create_rss_source(client) -> str:
    response = client.post(
        "/api/v1/radar/sources",
        json={
            "name": "RSS publico ficticio",
            "source_type": "public_feed",
            "url": "https://example.com/jobs.xml",
            "max_results": 10,
            "rate_limit_seconds": 0.2,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["source"]["id"]


def test_scheduler_crud_run_now_notifications_and_cooldown(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("modules.scraping.client.ScrapingClient.fetch", _fake_fetch)
    client = api_client()
    wishlist_id = _create_wishlist(client)
    source_id = _create_rss_source(client)

    create = client.post(
        "/api/v1/radar/schedules",
        json={
            "name": "Radar diario engenharia",
            "wishlist_id": wishlist_id,
            "source_ids": [source_id],
            "frequency": "daily",
            "cooldown_minutes": 720,
            "use_profile_context": True,
        },
    )
    assert create.status_code == 200
    schedule = create.json()["data"]["schedule"]
    assert schedule["enabled"] is True
    assert schedule["next_run_at"]

    listed = client.get("/api/v1/radar/schedules")
    assert listed.status_code == 200
    assert len(listed.json()["data"]["schedules"]) == 1

    patched = client.patch(
        f"/api/v1/radar/schedules/{schedule['schedule_id']}",
        json={"frequency": "custom_interval", "interval_minutes": 120},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["schedule"]["interval_minutes"] == 120

    first_run = client.post(f"/api/v1/radar/schedules/{schedule['schedule_id']}/run-now")
    assert first_run.status_code == 200
    first_payload = first_run.json()["data"]
    assert first_payload["scheduled_run"]["status"] in {"success", "warning"}
    assert first_payload["scheduled_run"]["total_results"] == 1
    assert first_payload["scheduled_run"]["alerts_created"] == 1
    assert first_payload["scheduled_run"]["metadata"]["auto_apply"] is False

    second_run = client.post(f"/api/v1/radar/schedules/{schedule['schedule_id']}/run-now")
    assert second_run.status_code == 200
    second_payload = second_run.json()["data"]
    assert second_payload["scheduled_run"]["alerts_created"] == 0

    notifications = client.get("/api/v1/notifications")
    assert notifications.status_code == 200
    notification = notifications.json()["data"]["notifications"][0]
    assert notification["read_at"] is None
    assert "api_key" not in json.dumps(notifications.json()).lower()

    read = client.patch(
        f"/api/v1/notifications/{notification['notification_id']}", json={"read": True}
    )
    assert read.status_code == 200
    assert read.json()["data"]["notification"]["read_at"]

    marked = client.post("/api/v1/notifications/mark-all-read")
    assert marked.status_code == 200
    cleared = client.delete("/api/v1/notifications/read")
    assert cleared.status_code == 200

    disabled = client.delete(f"/api/v1/radar/schedules/{schedule['schedule_id']}")
    assert disabled.status_code == 200
    assert disabled.json()["data"]["schedule"]["enabled"] is False


def test_scheduler_quiet_hours_skips_due_schedule(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    service = ScheduledRadarService()
    schedule = service.create_schedule(
        RadarSchedule(
            name="Radar silencioso",
            frequency="hourly",
            quiet_hours_start="00:00",
            quiet_hours_end="23:59",
            source_ids=[],
        )
    )
    store = RadarScheduleStore()
    state = store.load()
    state.schedules[0] = schedule.model_copy(
        update={"next_run_at": utc_now() - timedelta(minutes=1)}
    )
    store.save(state)

    runs = service.run_due_once()

    assert runs
    assert runs[0].status == "skipped"
    assert "Horario silencioso" in runs[0].warnings[0]


def test_scheduler_handles_no_active_source_with_warning(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    schedule = client.post(
        "/api/v1/radar/schedules",
        json={"name": "Radar sem fonte", "keywords": ["enfermagem", "COREN"]},
    ).json()["data"]["schedule"]

    response = client.post(f"/api/v1/radar/schedules/{schedule['schedule_id']}/run-now")

    assert response.status_code == 200
    scheduled_run = response.json()["data"]["scheduled_run"]
    assert scheduled_run["status"] == "warning"
    assert any("Nenhuma fonte ativa" in warning for warning in scheduled_run["warnings"])


def test_scheduler_uses_profile_context_when_enabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("modules.scraping.client.ScrapingClient.fetch", _fake_fetch)
    client = api_client()
    client.post(
        "/api/v1/profile/items",
        json={
            "type": "certification",
            "title": "NR10",
            "domain": "Engenharia",
            "evidence": "Certificado NR10 informado pelo usuario.",
        },
    )
    wishlist_id = _create_wishlist(client)
    source_id = _create_rss_source(client)
    schedule = client.post(
        "/api/v1/radar/schedules",
        json={
            "name": "Radar com perfil",
            "wishlist_id": wishlist_id,
            "source_ids": [source_id],
            "use_profile_context": True,
        },
    ).json()["data"]["schedule"]

    response = client.post(f"/api/v1/radar/schedules/{schedule['schedule_id']}/run-now")

    assert response.status_code == 200
    assert response.json()["data"]["scheduled_run"]["profile_context_used"] is True


def test_authenticated_assisted_capture_source_is_schedulable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    source = client.post(
        "/api/v1/radar/sources",
        json={
            "name": "Captura assistida login manual",
            "source_type": "authenticated_assisted_capture",
            "url": "https://example.invalid/minha-conta/vaga",
            "status": "available",
        },
    )
    assert source.status_code == 200
    source_id = source.json()["data"]["source"]["id"]
    schedule = client.post(
        "/api/v1/radar/schedules",
        json={"name": "Lembrete captura assistida", "source_ids": [source_id]},
    ).json()["data"]["schedule"]

    response = client.post(f"/api/v1/radar/schedules/{schedule['schedule_id']}/run-now")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["scheduled_run"]["status"] == "warning"
    assert payload["data"]["scheduled_run"]["alerts_created"] >= 1
    serialized = json.dumps(payload).lower()
    assert "auto_apply" in serialized
    assert "api_key" not in serialized


def test_scheduler_openapi_contains_new_endpoints(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    schema = app.openapi()
    paths = schema["paths"]
    expected = [
        "/api/v1/radar/schedules",
        "/api/v1/radar/schedules/{schedule_id}",
        "/api/v1/radar/schedules/{schedule_id}/run-now",
        "/api/v1/radar/scheduled-runs",
        "/api/v1/radar/scheduler/status",
        "/api/v1/radar/scheduler/start",
        "/api/v1/radar/scheduler/stop",
        "/api/v1/notifications",
        "/api/v1/notifications/{notification_id}",
        "/api/v1/notifications/mark-all-read",
    ]
    assert not [path for path in expected if path not in paths]
