"""Capture reproducible SotuHire screenshots with fictitious demo data."""

from __future__ import annotations

import argparse
from pathlib import Path

from modules.opportunities import OpportunityStore
from modules.scraping.connectors.manual_url import opportunity_from_text
from playwright.sync_api import Page, sync_playwright

OUTPUT_DIR = Path("docs/assets/screenshots")


def _wait(page: Page) -> None:
    page.wait_for_timeout(1200)
    page.wait_for_load_state("networkidle")


def _screenshot(page: Page, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUTPUT_DIR / name), full_page=False)


def _seed_fictitious_opportunities() -> None:
    """Populate the ignored local store with a reproducible fictitious opportunity."""
    opportunity = opportunity_from_text(
        (
            "Cargo: Desenvolvedor Python Júnior\nEmpresa: Example Tech\n"
            "Localização: Remoto\nVaga CLT para Python, SQL, Git e Docker."
        ),
        source="Fixture pública Example Tech",
        source_url="https://example.com/jobs/python-junior",
    )
    OpportunityStore().save_many([opportunity])


def capture(base_url: str) -> None:
    """Capture v0.7 quick, advanced, collection, search, result, and dashboard surfaces."""
    _seed_fictitious_opportunities()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 980}, device_scale_factor=1)
        page.goto(base_url, wait_until="networkidle")
        _wait(page)
        _screenshot(page, "sotuhire-v0.7-quick-mode.png")

        page.get_by_role("button", name="Rodar demo completa").first.click()
        _wait(page)
        page.get_by_text("Resultado", exact=True).last.scroll_into_view_if_needed()
        _screenshot(page, "sotuhire-v0.7-result.png")

        page.get_by_text("Modo avançado", exact=True).first.click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.7-advanced-mode.png")

        page.get_by_role("tab", name="Coletar vagas").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.7-collect-jobs.png")
        page.get_by_text("Oportunidades coletadas", exact=True).scroll_into_view_if_needed()
        _screenshot(page, "sotuhire-v0.7-collected-opportunities.png")

        page.get_by_role("tab", name="Search Intelligence").click()
        _wait(page)
        page.get_by_role("tab", name="Fontes").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.7-search-intelligence.png")
        page.get_by_role("tab", name="Radar oculto").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.7-hidden-radar.png")

        page.get_by_role("tab", name="Resultado").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.7-result.png")
        page.get_by_role("tab", name="Dashboard").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.7-dashboard.png")
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    args = parser.parse_args()
    capture(args.url)


if __name__ == "__main__":
    main()
