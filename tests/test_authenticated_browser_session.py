import json
from pathlib import Path

import pytest
from modules.scraping.browser_session import (
    BrowserSessionStatus,
    inspect_browser_session,
    launch_authenticated_browser,
    normalize_cdp_endpoint,
)


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args: object):
        return None

    def read(self) -> bytes:
        return json.dumps(
            {
                "Browser": "Chrome/Test",
                "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/test",
            }
        ).encode()


def test_cdp_endpoint_accepts_only_local_http():
    assert normalize_cdp_endpoint("http://127.0.0.1:9222/") == "http://127.0.0.1:9222"

    with pytest.raises(ValueError):
        normalize_cdp_endpoint("https://remote.example:9222")


def test_invalid_cdp_endpoint_returns_friendly_status():
    status = inspect_browser_session("https://remote.example:9222")

    assert not status.available
    assert "HTTP local" in status.message


def test_inspect_browser_session_reports_connected_browser():
    status = inspect_browser_session(
        "http://127.0.0.1:9222",
        opener=lambda *args, **kwargs: FakeResponse(),
    )

    assert status.available
    assert status.browser == "Chrome/Test"


def test_launch_authenticated_browser_uses_persistent_profile(tmp_path: Path):
    statuses = iter(
        [
            BrowserSessionStatus(False, "http://127.0.0.1:9222"),
            BrowserSessionStatus(True, "http://127.0.0.1:9222", browser="Chrome/Test"),
        ]
    )
    calls: list[list[str]] = []

    status = launch_authenticated_browser(
        "https://www.linkedin.com/jobs/",
        executable=tmp_path / "chrome.exe",
        profile_dir=tmp_path / "profile",
        popen=lambda command, **kwargs: calls.append(command),
        sleeper=lambda seconds: None,
        status_checker=lambda endpoint: next(statuses),
    )

    assert status.available
    assert calls
    assert "--remote-debugging-port=9222" in calls[0]
    assert any(argument.startswith("--user-data-dir=") for argument in calls[0])
