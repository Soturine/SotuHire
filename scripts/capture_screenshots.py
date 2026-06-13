"""Capture reproducible SotuHire screenshots with fictitious demo data."""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

OUTPUT_DIR = Path("docs/assets/screenshots")


def _wait(page: Page) -> None:
    page.wait_for_timeout(1200)
    page.wait_for_load_state("networkidle")


def _screenshot(page: Page, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUTPUT_DIR / name), full_page=False)


def capture(base_url: str) -> None:
    """Capture quick, advanced, result, dashboard, and AI setup surfaces."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 980}, device_scale_factor=1)
        page.goto(base_url, wait_until="networkidle")
        _wait(page)
        _screenshot(page, "sotuhire-v0.6-home.png")

        page.get_by_role("button", name="Rodar demo completa").first.click()
        _wait(page)
        page.get_by_text("Resultado", exact=True).last.scroll_into_view_if_needed()
        _screenshot(page, "sotuhire-v0.6-result.png")

        page.get_by_text("Modo avançado", exact=True).first.click()
        _wait(page)
        page.get_by_role("tab", name="Currículo").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.6-resume.png")

        page.get_by_role("tab", name="Vaga").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.6-job.png")

        page.get_by_role("tab", name="Dashboard").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.6-dashboard.png")

        page.get_by_text("Configurar IA", exact=True).click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.6-ai-setup.png")
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    args = parser.parse_args()
    capture(args.url)


if __name__ == "__main__":
    main()
