"""CP-UX02: variants refuse stale writes, and Profile edits reach the Master only on request.

Before: two tabs editing the same variant were last-write-wins (the second autosave silently
erased the first), and a fact edited in the Profile after it was projected into the Master
Resume never showed up anywhere: the Master kept the old text with no signal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from modules.application_lab.profile_projection import (
    master_resume_from_profile,
    profile_changes,
    refresh_profile_facts,
)
from modules.application_lab.repository import (
    ApplicationLabRepository,
    ResumeVariantConflictError,
)
from modules.profile.models import ProfileItem
from modules.profile.service import UniversalCareerProfileService
from tests.api_test_helpers import api_client

STUDIO = "/api/v1/resume-studio"


@pytest.fixture
def profile(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    service = UniversalCareerProfileService()
    service.add_item(
        ProfileItem(type="experience", title="Enfermeira assistencial", description="UTI adulto")
    )
    return service


def _variant(client) -> dict:
    master = client.post(f"{STUDIO}/master/from-profile", json={}).json()["data"]["resume"]
    variant = {
        "resume_variant_id": "variant-fixture",
        "master_resume_id": master["master_resume_id"],
        "title": "Variante",
        "target_role": "Enfermeira",
        "sections": master["sections"],
    }
    created = client.post(f"{STUDIO}/variants", json={"variant": variant})
    assert created.status_code == 200, created.text
    return created.json()["data"]["variant"]


def test_a_variant_patch_from_a_stale_copy_answers_409_and_keeps_the_newer(profile) -> None:
    client = api_client()
    loaded = _variant(client)
    url = f"{STUDIO}/variants/{loaded['resume_variant_id']}"

    first = client.patch(url, json={"title": "Aba 1", "expected_updated_at": loaded["updated_at"]})
    assert first.status_code == 200, first.text
    second = client.patch(url, json={"title": "Aba 2", "expected_updated_at": loaded["updated_at"]})
    assert second.status_code == 409
    assert client.get(url).json()["data"]["variant"]["title"] == "Aba 1"
    # the editor can still overwrite on purpose (explicit "keep mine")
    assert client.patch(url, json={"title": "Aba 2"}).status_code == 200


def test_conditional_variant_writes_cannot_both_win(profile, tmp_path: Path) -> None:
    client = api_client()
    loaded = _variant(client)
    repository = ApplicationLabRepository(tmp_path / "sotuhire.db")
    stored = repository.get_variant(loaded["resume_variant_id"])
    assert stored is not None
    expected = stored.updated_at
    # each writer stamps a new version, as the service does
    first = stored.model_copy(update={"title": "A", "updated_at": datetime.now(UTC)})
    repository.save_variant(first, expected_updated_at=expected)
    second = stored.model_copy(update={"title": "B", "updated_at": datetime.now(UTC)})
    with pytest.raises(ResumeVariantConflictError):
        repository.save_variant(second, expected_updated_at=expected)
    current = repository.get_variant(stored.resume_variant_id)
    assert current is not None and current.title == "A"


def test_an_edited_profile_fact_is_listed_with_before_and_after(profile) -> None:
    master = master_resume_from_profile(profile.get_profile())
    item = profile.get_profile().items[0]
    profile.patch_item(item.item_id, {"description": "UTI adulto e pediátrica"})

    changes = profile_changes(profile.get_profile(), master)

    assert [(changed.item_id, diff) for changed, _section, diff in changes] == [
        (item.item_id, {"content": ("UTI adulto", "UTI adulto e pediátrica")})
    ]


def test_refresh_updates_the_master_entry_only_and_is_idempotent(profile) -> None:
    master = master_resume_from_profile(profile.get_profile())
    entry_before = master.sections[0].entries[0]
    item = profile.get_profile().items[0]
    profile.patch_item(item.item_id, {"description": "UTI adulto e pediátrica"})

    refreshed = refresh_profile_facts(master, profile.get_profile(), [item.item_id])
    entry = refreshed.sections[0].entries[0]
    assert entry.content == "UTI adulto e pediátrica"
    assert (entry.entry_id, entry.enabled) == (entry_before.entry_id, entry_before.enabled)
    assert profile_changes(profile.get_profile(), refreshed) == []
    assert refresh_profile_facts(refreshed, profile.get_profile(), [item.item_id]) is refreshed
    # the Master is not the authority for the Profile: nothing flowed back
    assert profile.get_profile().items[0].description == "UTI adulto e pediátrica"


def test_refresh_refuses_facts_that_are_not_in_the_master(profile) -> None:
    master = master_resume_from_profile(profile.get_profile())
    later = profile.add_item(ProfileItem(type="language", title="Inglês"))
    with pytest.raises(ValueError, match="não estão no Currículo Mestre"):
        refresh_profile_facts(master, profile.get_profile(), [later.item_id, "missing"])


def test_the_api_lists_changed_facts_and_refreshes_on_request(profile) -> None:
    client = api_client()
    assert client.post(f"{STUDIO}/master/from-profile", json={}).status_code == 201
    item = profile.get_profile().items[0]
    profile.patch_item(item.item_id, {"title": "Enfermeira intensivista"})

    listed = client.get(f"{STUDIO}/master/profile-updates").json()["data"]
    assert listed["items"] == []
    assert listed["changed"][0]["item_id"] == item.item_id
    assert listed["changed"][0]["changes"] == [
        {
            "field": "title",
            "in_master": "Enfermeira assistencial",
            "in_profile": "Enfermeira intensivista",
        }
    ]

    refreshed = client.post(f"{STUDIO}/master/profile-refresh", json={"item_ids": [item.item_id]})
    assert refreshed.status_code == 200, refreshed.text
    retry = client.post(f"{STUDIO}/master/profile-refresh", json={"item_ids": [item.item_id]})
    assert retry.json()["data"]["resume"] == refreshed.json()["data"]["resume"]
    assert client.get(f"{STUDIO}/master/profile-updates").json()["data"]["changed"] == []
