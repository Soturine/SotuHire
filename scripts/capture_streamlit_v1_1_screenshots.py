"""Capture v1.1 README screenshots from the real Streamlit app."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import sleep

from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.capture_screenshots import (  # noqa: E402
    _restore_local_state,
    _screenshot,
    _seed_fictitious_companion,
    _seed_fictitious_memory,
    _seed_fictitious_opportunities,
    _seed_fictitious_project,
    _snapshot_local_state,
    _wait,
)


def _capture_readme_preview(page: Page) -> None:
    page.locator("body").evaluate("window.scrollTo(0, 0)")
    _wait(page)
    _screenshot(page, "sotuhire-v1.1-streamlit-home.png")

    page.get_by_role("button", name="Rodar demo completa").first.click()
    _wait(page)

    page.get_by_text("Modo avançado", exact=True).first.click()
    _wait(page)
    page.get_by_role("tab", name="Resultado").first.click()
    _wait(page)
    page.get_by_text("Match Engine 2.0", exact=True).first.scroll_into_view_if_needed()
    _wait(page)
    _screenshot(page, "sotuhire-v1.1-streamlit-match.png")

    page.get_by_role("tab", name="Dashboard").click()
    _wait(page)
    _screenshot(page, "sotuhire-v1.1-streamlit-dashboard.png")


def capture(base_url: str) -> None:
    snapshot = _snapshot_local_state()
    try:
        _seed_fictitious_opportunities()
        _seed_fictitious_memory()
        _seed_fictitious_companion()
        _seed_fictitious_project()

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 980}, device_scale_factor=1)
            page.goto(base_url, wait_until="networkidle")
            _wait(page)
            _capture_readme_preview(page)
            browser.close()
    finally:
        sleep(2)
        _restore_local_state(snapshot)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    args = parser.parse_args()
    capture(args.url)


if __name__ == "__main__":
    main()
