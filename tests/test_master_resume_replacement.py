"""Re-importing a resume never takes the place of the current Master Resume without consent.

The Resume Studio offers "Importar outro currículo para o Mestre" while a Master exists. Adopting
that draft (its own master_resume_id) used to be a blind upsert: the imported resume became the
Master the app shows, the one being edited disappeared from view, and its variants stayed tied to
it. Now the API refuses unless the client says the person confirmed the replacement, and the
confirmation names the Master they saw.
"""

from __future__ import annotations

from tests.test_application_lab_api import _client, _master

MASTER = "/api/v1/resume-studio/master"


def _imported() -> dict:
    draft = _master().model_copy(
        update={"master_resume_id": "master-imported", "title": "Currículo reimportado"}
    )
    return draft.model_dump(mode="json")


def _current(client) -> dict:
    return client.get(MASTER).json()["data"]["resume"]


def test_an_imported_resume_does_not_replace_the_master_without_confirmation(tmp_path) -> None:
    client, _ = _client(tmp_path)
    assert client.put(MASTER, json={"resume": _master().model_dump(mode="json")}).status_code == 200
    before = _current(client)

    response = client.put(MASTER, json={"resume": _imported()})

    assert response.status_code == 409
    assert "confirme a substituição" in response.json()["error"]["message"]
    assert _current(client) == before


def test_a_confirmed_replacement_keeps_the_previous_master_stored(tmp_path) -> None:
    client, service = _client(tmp_path)
    client.put(MASTER, json={"resume": _master().model_dump(mode="json")})
    shown = _current(client)

    response = client.put(
        MASTER,
        json={
            "resume": _imported(),
            "replace_existing": True,
            "expected_updated_at": shown["updated_at"],
        },
    )

    assert response.status_code == 200
    assert _current(client)["master_resume_id"] == "master-imported"
    previous = service.repository.get_master_resume("master-api")
    assert previous is not None and previous.title == shown["title"]  # replaced, not deleted


def test_a_replacement_confirmed_on_an_outdated_view_is_refused(tmp_path) -> None:
    client, _ = _client(tmp_path)
    client.put(MASTER, json={"resume": _master().model_dump(mode="json")})
    seen = _current(client)
    edited = _master().model_copy(update={"summary": "Editado em outra aba."})
    client.put(
        MASTER,
        json={"resume": edited.model_dump(mode="json"), "expected_updated_at": seen["updated_at"]},
    )

    response = client.put(
        MASTER,
        json={
            "resume": _imported(),
            "replace_existing": True,
            "expected_updated_at": seen["updated_at"],
        },
    )

    assert response.status_code == 409
    assert _current(client)["summary"] == "Editado em outra aba."


def test_first_import_and_editing_the_current_master_still_work(tmp_path) -> None:
    client, _ = _client(tmp_path)
    assert client.put(MASTER, json={"resume": _imported()}).status_code == 200  # no Master yet
    current = _current(client)
    current["summary"] = "Resumo revisado."
    response = client.put(
        MASTER, json={"resume": current, "expected_updated_at": current["updated_at"]}
    )
    assert response.status_code == 200
    assert _current(client)["summary"] == "Resumo revisado."
