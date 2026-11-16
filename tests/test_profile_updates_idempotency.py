"""Applying profile facts to the Master Resume is idempotent and refuses stale writes.

Reproduces three defects of the first version of ``apply_profile_updates``:

* a request with a repeated id appended the same fact twice (the ids were deduplicated for the
  check, but the original list was iterated to build entries);
* a retry of a request that already succeeded answered 422, so a client that lost the response
  could not tell success from failure;
* two writers that loaded the same Master Resume both saved it, and the last one silently dropped
  what the first had added (lost update).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from apps.api.services.application_lab import ApplicationLabApiService
from fastapi import HTTPException
from modules.application_lab.profile_projection import (
    apply_profile_updates,
    master_resume_from_profile,
)
from modules.application_lab.repository import (
    ApplicationLabRepository,
    MasterResumeConflictError,
)
from modules.profile.models import ProfileItem
from modules.profile.service import UniversalCareerProfileService
from tests.api_test_helpers import api_client

STUDIO = "/api/v1/resume-studio"


def _entries_for(resume, item_id: str) -> int:
    return sum(
        item_id in entry.source_profile_item_ids
        for section in resume.sections
        for entry in section.entries
    )


@pytest.fixture
def profile(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    service = UniversalCareerProfileService()
    service.add_item(ProfileItem(type="experience", title="Enfermeira assistencial"))
    return service


def test_a_repeated_id_adds_the_fact_once(profile) -> None:
    master = master_resume_from_profile(profile.get_profile())
    added = profile.add_item(ProfileItem(type="language", title="Inglês intermediário"))

    updated = apply_profile_updates(
        master, profile.get_profile(), [added.item_id, added.item_id, added.item_id]
    )

    assert _entries_for(updated, added.item_id) == 1
    assert updated.source_profile_item_ids.count(added.item_id) == 1


def test_applying_a_fact_that_is_already_there_changes_nothing(profile) -> None:
    master = master_resume_from_profile(profile.get_profile())
    added = profile.add_item(ProfileItem(type="language", title="Inglês intermediário"))
    once = apply_profile_updates(master, profile.get_profile(), [added.item_id])

    again = apply_profile_updates(once, profile.get_profile(), [added.item_id])

    assert again == once  # same object state, same updated_at: nothing to save


def test_a_retried_request_answers_200_with_the_same_resume(profile) -> None:
    client = api_client()
    assert client.post(f"{STUDIO}/master/from-profile", json={}).status_code == 201
    added = profile.add_item(ProfileItem(type="language", title="Inglês intermediário"))

    first = client.post(f"{STUDIO}/master/profile-updates", json={"item_ids": [added.item_id]})
    retry = client.post(f"{STUDIO}/master/profile-updates", json={"item_ids": [added.item_id]})

    assert first.status_code == retry.status_code == 200, retry.text
    assert retry.json()["data"]["resume"] == first.json()["data"]["resume"]
    titles = [
        entry["title"]
        for section in retry.json()["data"]["resume"]["sections"]
        for entry in section["entries"]
    ]
    assert titles.count("Inglês intermediário") == 1


def test_ids_that_are_not_projectable_are_still_refused(profile) -> None:
    master = master_resume_from_profile(profile.get_profile())
    candidate = profile.add_item(
        ProfileItem(type="experience", title="Estágio não revisado"), confirmed_by_user=False
    )
    with pytest.raises(ValueError, match="não confirmados"):
        apply_profile_updates(master, profile.get_profile(), [candidate.item_id, "missing"])


def test_a_write_based_on_a_stale_copy_is_refused(profile, tmp_path: Path) -> None:
    repository = ApplicationLabRepository(tmp_path / "sotuhire.db")
    saved = repository.save_master_resume(master_resume_from_profile(profile.get_profile()))
    stale = repository.get_master_resume(saved.master_resume_id)
    assert stale is not None

    first = profile.add_item(ProfileItem(type="language", title="Inglês intermediário"))
    winner = apply_profile_updates(stale, profile.get_profile(), [first.item_id])
    repository.save_master_resume(winner, expected_updated_at=stale.updated_at)

    second = profile.add_item(ProfileItem(type="language", title="Espanhol básico"))
    loser = apply_profile_updates(stale, profile.get_profile(), [second.item_id])
    with pytest.raises(MasterResumeConflictError):
        repository.save_master_resume(loser, expected_updated_at=stale.updated_at)

    current = repository.get_master_resume(saved.master_resume_id)
    assert current is not None
    assert _entries_for(current, first.item_id) == 1  # the first writer's fact survived


def test_the_api_maps_a_stale_write_to_409(profile, monkeypatch) -> None:
    service = ApplicationLabApiService()
    service.master_from_profile()
    added = profile.add_item(ProfileItem(type="language", title="Inglês intermediário"))

    real_get = service.repository.get_master_resume
    other_tab_saved = False

    def stale_get(master_resume_id: str = ""):
        nonlocal other_tab_saved
        snapshot = real_get(master_resume_id)
        assert snapshot is not None
        if not other_tab_saved:
            # another tab saves once between this read and the write below (save_master reads
            # the current Master too, so the interference must not repeat on that read)
            other_tab_saved = True
            service.save_master(snapshot.model_copy(update={"title": "Outra aba"}))
        return snapshot

    monkeypatch.setattr(service.repository, "get_master_resume", stale_get)
    with pytest.raises(HTTPException) as raised:
        service.apply_profile_updates([added.item_id])
    assert raised.value.status_code == 409


def test_put_with_an_old_expected_version_answers_409_and_keeps_the_newer_copy(profile) -> None:
    client = api_client()
    resume = client.post(f"{STUDIO}/master/from-profile", json={}).json()["data"]["resume"]
    loaded_at = resume["updated_at"]

    newer = client.put(
        f"{STUDIO}/master",
        json={"resume": {**resume, "title": "Aba 1"}, "expected_updated_at": loaded_at},
    )
    assert newer.status_code == 200, newer.text
    stale = client.put(
        f"{STUDIO}/master",
        json={"resume": {**resume, "title": "Aba 2"}, "expected_updated_at": loaded_at},
    )
    assert stale.status_code == 409
    assert client.get(f"{STUDIO}/master").json()["data"]["resume"]["title"] == "Aba 1"
    # without a version the PUT stays an upsert (adopting an imported draft)
    assert client.put(f"{STUDIO}/master", json={"resume": resume}).status_code == 200
