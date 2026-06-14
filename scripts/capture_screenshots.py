"""Capture reproducible SotuHire screenshots with fictitious demo data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

OUTPUT_DIR = Path("docs/assets/screenshots")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _wait(page: Page) -> None:
    page.wait_for_timeout(1200)
    page.wait_for_load_state("networkidle")


def _screenshot(page: Page, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUTPUT_DIR / name), full_page=False)


def _seed_fictitious_opportunities() -> None:
    """Populate the ignored local store with a reproducible fictitious opportunity."""
    from modules.opportunities import OpportunityStore
    from modules.scraping.connectors.manual_url import opportunity_from_text

    opportunity = opportunity_from_text(
        (
            "Cargo: Desenvolvedor Python Júnior\nEmpresa: Example Tech\n"
            "Localização: Remoto\nVaga CLT para Python, SQL, Git e Docker."
        ),
        source="Fixture pública Example Tech",
        source_url="https://example.com/jobs/python-junior",
    )
    OpportunityStore().save_many([opportunity])


def _seed_fictitious_memory() -> None:
    """Populate ignored local memory with reproducible fictitious career facts."""
    from modules.memory import CareerMemoryItem, MemoryStore

    store = MemoryStore()
    store.clear()
    items = [
        CareerMemoryItem(
            kind="project",
            title="Projeto Atlas IoT",
            content="Monitoramento industrial fictício com ESP32, Python e MQTT.",
            source="demo",
            tags=["ESP32", "Python", "MQTT", "IoT"],
        ),
        CareerMemoryItem(
            kind="experience",
            title="Experiência técnica industrial",
            content="Apoio fictício a processos técnicos e documentação industrial.",
            source="demo",
            tags=["processos", "indústria", "documentação"],
        ),
        CareerMemoryItem(
            kind="job_analysis",
            title="Análise: Desenvolvedor Python Júnior · Example Tech",
            content=(
                "Recomendação: apply_with_adjustments. Match: 78. ATS: 74. Fit: 85. "
                "Fortes: Python, SQL. Gaps: Docker."
            ),
            source="demo",
            tags=["Python", "SQL", "apply_with_adjustments"],
        ),
        CareerMemoryItem(
            kind="preference",
            title="Modalidades preferidas",
            content="remote, hybrid",
            source="demo",
            tags=["remote", "hybrid"],
        ),
    ]
    for item in items:
        store.add_memory_item(item)


def capture(base_url: str) -> None:
    """Capture current app surfaces using only fictitious local data."""
    _seed_fictitious_opportunities()
    _seed_fictitious_memory()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 980}, device_scale_factor=1)
        page.goto(base_url, wait_until="networkidle")
        _wait(page)

        page.get_by_role("button", name="Rodar demo completa").first.click()
        _wait(page)

        page.get_by_text("Modo avançado", exact=True).first.click()
        _wait(page)

        page.get_by_role("tab", name="Memória de carreira").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.8-memory-overview.png")

        page.get_by_role("tab", name="Perfil profissional").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.8-career-profile.png")

        page.get_by_role("tab", name="Buscar").click()
        page.get_by_label("Buscar na memória").fill("Python")
        page.get_by_label("Buscar na memória").press("Enter")
        _wait(page)
        _screenshot(page, "sotuhire-v0.8-memory-search.png")

        page.get_by_role("tab", name="Resultado").first.click()
        _wait(page)
        page.get_by_role("tab", name="Evidências").click()
        _wait(page)
        _screenshot(page, "sotuhire-v0.8-evidence-analysis.png")
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    args = parser.parse_args()
    capture(args.url)


if __name__ == "__main__":
    main()
