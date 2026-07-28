from pathlib import Path


def test_popup_opens_application_lab_with_identifiers_only() -> None:
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")
    html = Path("browser-extension/popup.html").read_text(encoding="utf-8")

    assert 'data-action="prepare-application"' in html
    assert "Preparar candidatura" in html
    flow = popup.split("async function prepareApplication()", maxsplit=1)[1].split(
        "const act =", maxsplit=1
    )[0]
    assert 'sendOrQueue("/capture/job", capture' in flow
    assert 'new URL("/application-lab"' in flow
    assert 'target.searchParams.set("capture_id", saved.capture_id)' in flow
    assert 'target.searchParams.set("job_snapshot_id", saved.snapshot_id)' in flow
    assert "chrome.tabs.create" in flow
    target_section = flow.split("const target =", maxsplit=1)[1]
    assert "visible_text" not in target_section
    assert "profile_summary" not in target_section
    assert "resume_text" not in target_section


def test_application_lab_action_preserves_existing_offline_queue_contract() -> None:
    popup = Path("browser-extension/popup.js").read_text(encoding="utf-8")

    assert "pendingCompanionActions" in popup
    assert 'sendOrQueue("/capture/job", capture, "Vaga para o Application Lab")' in popup
    assert "queuePendingAction(path, body, label)" in popup
