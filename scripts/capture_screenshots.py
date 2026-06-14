"""Capture reproducible SotuHire screenshots with fictitious demo data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

OUTPUT_DIR = Path("docs/assets/screenshots")
LOCAL_STATE_PATHS = (
    Path("data/memory/career-memory.jsonl"),
    Path("data/memory/career-profile.json"),
    Path("data/sotuhire-opportunities.json"),
    Path("data/sotuhire-history.json"),
    Path("data/companion/captures.jsonl"),
    Path("data/companion/active-context.json"),
    Path("data/portfolio/project-analyses.jsonl"),
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _wait(page: Page) -> None:
    page.wait_for_timeout(1200)
    page.wait_for_load_state("networkidle")


def _screenshot(page: Page, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUTPUT_DIR / name), full_page=False)


def _snapshot_local_state() -> dict[Path, bytes | None]:
    """Read local stores so screenshot fixtures never replace user data."""
    return {path: path.read_bytes() if path.exists() else None for path in LOCAL_STATE_PATHS}


def _restore_local_state(snapshot: dict[Path, bytes | None]) -> None:
    """Restore or remove stores according to their state before capture."""
    for path, content in snapshot.items():
        if content is None:
            path.unlink(missing_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.screenshot-restore.tmp")
        temporary.write_bytes(content)
        temporary.replace(path)


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


def _seed_fictitious_companion() -> None:
    """Populate captures and tracker with one fictitious multiportal application."""
    from modules.local_api import BrowserCapturePayload, LocalCompanionService

    service = LocalCompanionService()
    first = BrowserCapturePayload(
        page_title="Pessoa Desenvolvedora Python Júnior",
        job_title="Pessoa Desenvolvedora Python Júnior",
        company="Example Tech",
        location="Brasil (Remoto)",
        url="https://network.example/jobs/view/123",
        domain="network.example",
        description="Vaga fictícia para Python, SQL, FastAPI e Git.",
    )
    second = first.model_copy(
        update={
            "page_title": "Desenvolvedora Python Junior",
            "job_title": "Desenvolvedora Python Junior",
            "url": "https://careers.example/jobs/python-junior",
            "domain": "careers.example",
        }
    )
    service.capture_job(first)
    service.capture_job(second)
    service.tracker.add_existing_application(
        job_title=first.job_title,
        company=first.company,
        source_url=first.url,
        requirements=["Python", "SQL", "FastAPI", "Git"],
    )
    service.tracker.add_existing_application(
        job_title=second.job_title,
        company=second.company,
        source_url=second.url,
        requirements=["Python", "SQL", "FastAPI", "Git"],
    )


def _seed_fictitious_project() -> None:
    """Populate one reproducible public repository report and project evidence."""
    from modules.local_api import LocalCompanionService
    from modules.portfolio import ProjectAnalysisPayload

    LocalCompanionService().analyze_project_capture(
        ProjectAnalysisPayload(
            url="https://github.example/example/atlas-api",
            owner="example",
            repo="atlas-api",
            title="Atlas API",
            page_type="github_repo",
            visible_text="API fictícia para monitoramento com Python, FastAPI, SQL e Docker.",
            readme_text=(
                "Atlas API\nInstallation\nUsage\nArchitecture\n"
                "API fictícia com Python, FastAPI, SQL, Docker e testes automatizados."
            ),
            files_sampled=[
                "README.md",
                "pyproject.toml",
                "Dockerfile",
                "src/api.py",
                "modules/monitoring.py",
                "tests/test_api.py",
                "docs/architecture.md",
                ".github/workflows/ci.yml",
            ],
            commit_messages=[
                "feat: add monitoring endpoint",
                "test: cover monitoring endpoint",
                "docs: explain local setup",
                "fix(api): validate sensor payload",
            ],
            languages=["Python", "SQL"],
            topics=["FastAPI", "Docker", "IoT"],
        )
    )


def _capture_github_extension_mock(browser, base_url: str) -> None:
    """Render the injected GitHub button and modal with controlled public demo data."""
    page = browser.new_page(viewport={"width": 1440, "height": 980}, device_scale_factor=1)
    page.goto(f"{base_url}/example/atlas-api", wait_until="domcontentloaded")
    page.set_content(
        """
        <style>
          body { margin: 0; color: #f0f6fc; background: #0d1117; font: 14px Arial; }
          header { padding: 18px 42px; border-bottom: 1px solid #30363d; }
          main { width: 1120px; margin: 28px auto; }
          .file-navigation { display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 14px; }
          .repo { display: grid; grid-template-columns: 1fr 280px; gap: 24px; }
          .panel, article { padding: 20px; border: 1px solid #30363d; border-radius: 8px; background: #161b22; }
          a { display: block; padding: 8px; color: #58a6ff; }
        </style>
        <header>GitHub · example / atlas-api</header>
        <main>
          <h1>example / atlas-api</h1>
          <div class="file-navigation"><button>Go to file</button><button>Code</button></div>
          <div class="repo">
            <section class="panel">
              <a href="/example/atlas-api/blob/main/README.md" title="README.md">README.md</a>
              <a href="/example/atlas-api/blob/main/pyproject.toml" title="pyproject.toml">pyproject.toml</a>
              <a href="/example/atlas-api/tree/main/src" title="src/api.py">src/api.py</a>
              <a href="/example/atlas-api/tree/main/tests" title="tests/test_api.py">tests/test_api.py</a>
              <a href="/example/atlas-api/tree/main/.github/workflows" title=".github/workflows/ci.yml">.github/workflows/ci.yml</a>
              <a href="/example/atlas-api/commit/1">feat: add monitoring endpoint</a>
              <a href="/example/atlas-api/commit/2">test: cover API endpoint</a>
            </section>
            <aside class="panel"><div class="language">Python</div><div class="topic">FastAPI</div><div class="topic">Docker</div></aside>
          </div>
          <article id="readme"><h2>Atlas API</h2><p>Installation, usage and architecture for a fictitious FastAPI monitoring service with tests.</p></article>
        </main>
        """
    )
    page.evaluate(
        """
        Object.defineProperty(window, "chrome", {value: {
          storage: {local: {
            get: async () => ({deepProjectAnalysis: true, useAI: false, standaloneGeminiKey: ""}),
            set: async () => ({})
          }},
          permissions: {request: async () => false}
        }});
        """
    )
    page.add_script_tag(path="browser-extension/project_analysis.js")
    page.add_script_tag(path="browser-extension/github_injected.js")
    page.wait_for_timeout(500)
    _screenshot(page, "sotuhire-v0.9-github-button.png")
    page.locator("#sotuhire-repo-button").click()
    page.wait_for_timeout(300)
    _screenshot(page, "sotuhire-v0.9-extension-settings.png")
    page.get_by_role("button", name="Analisar repositorio").click()
    page.wait_for_timeout(1800)
    _screenshot(page, "sotuhire-v0.9-extension-modal.png")
    _screenshot(page, "sotuhire-v0.9-repo-analysis-report.png")
    page.close()


def _capture_store_listing_mock(browser) -> None:
    """Render a controlled Chrome Web Store listing preview."""
    page = browser.new_page(viewport={"width": 1440, "height": 980}, device_scale_factor=1)
    page.set_content(
        """
        <style>
          body { margin: 0; padding: 48px; background: #f6f8fc; color: #172033; font: 16px Arial; }
          main { max-width: 1120px; margin: auto; }
          .hero { display: grid; grid-template-columns: 128px 1fr auto; gap: 24px; align-items: center; }
          .icon { width: 128px; height: 128px; border-radius: 28px; display: grid; place-items: center; background: #071425; color: white; font-size: 68px; font-weight: bold; }
          button { padding: 14px 28px; border: 0; border-radius: 24px; background: #1769e0; color: white; font-weight: bold; }
          .shots { display: grid; grid-template-columns: 2fr 1fr; gap: 18px; margin-top: 36px; }
          .card { min-height: 280px; padding: 28px; border-radius: 18px; background: #071425; color: white; box-shadow: 0 8px 30px #24324a22; }
          .score { color: #ff5369; font-size: 72px; font-weight: bold; }
          li { margin: 12px 0; }
        </style>
        <main>
          <section class="hero"><div class="icon">S</div><div><h1>SotuHire Assistive Browser Companion</h1><p>Analise projetos publicos do GitHub e capture vagas no seu SotuHire local.</p><strong>Produtividade · Privacidade local-first · v0.9.0</strong></div><button>Adicionar ao Chrome</button></section>
          <section class="shots"><div class="card"><h2>GitHub Analyzer</h2><div class="score">82 / 100 · A</div><p>README, commits, arquitetura, stack e evidencias para curriculo em um relatorio visual.</p></div><div class="card"><h2>Recursos</h2><ul><li>Botao injetado no GitHub</li><li>Modo standalone ou conectado</li><li>Captura assistida de vagas</li><li>Sem cookies ou tokens</li></ul></div></section>
        </main>
        """
    )
    _screenshot(page, "sotuhire-v0.9-store-listing.png")
    page.close()


def capture(base_url: str) -> None:
    """Capture current app surfaces using only fictitious local data."""
    from playwright.sync_api import sync_playwright

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

            page.get_by_role("button", name="Rodar demo completa").first.click()
            _wait(page)

            page.get_by_text("Modo avançado", exact=True).first.click()
            _wait(page)

            page.get_by_role("tab", name="Extensão").click()
            _wait(page)
            _screenshot(page, "sotuhire-v0.9-extension-tab.png")

            page.get_by_text("Últimas capturas recebidas").scroll_into_view_if_needed()
            _wait(page)
            _screenshot(page, "sotuhire-v0.9-captured-job.png")

            page.get_by_role("tab", name="Resultado").first.click()
            _wait(page)
            page.get_by_role("tab", name="Evidências").click()
            _wait(page)
            _screenshot(page, "sotuhire-v0.9-evidence-feedback.png")

            page.get_by_role("tab", name="Memória de carreira").click()
            _wait(page)
            page.get_by_role("tab", name="Perfil profissional").click()
            _wait(page)
            _screenshot(page, "sotuhire-v0.9-career-profile.png")

            popup = browser.new_page(viewport={"width": 420, "height": 1080}, device_scale_factor=1)
            popup.goto((Path("browser-extension/popup.html").resolve()).as_uri())
            popup.wait_for_timeout(500)
            _screenshot(popup, "sotuhire-v0.9-extension-popup.png")
            _screenshot(popup, "sotuhire-v0.9-extension-github-analysis.png")
            popup.locator("details").click()
            popup.wait_for_timeout(300)
            _screenshot(popup, "sotuhire-v0.9-extension-api-key.png")
            popup.close()

            _capture_github_extension_mock(browser, base_url)
            _capture_store_listing_mock(browser)

            page.get_by_role("tab", name="GitHub / Portfólio / Projetos").click()
            _wait(page)
            page.get_by_text("Atlas API · 72/100 · B", exact=True).click()
            _wait(page)
            _screenshot(page, "sotuhire-v0.9-extension-repo-report.png")
            _screenshot(page, "sotuhire-v0.9-github-profile-score.png")

            page.get_by_text("Arquivos e commits analisados").click()
            _wait(page)
            _screenshot(page, "sotuhire-v0.9-commit-analysis.png")

            page.get_by_role("tab", name="Memória de carreira").click()
            _wait(page)
            page.get_by_role("tab", name="Buscar").click()
            page.get_by_label("Buscar na memória").fill("FastAPI Docker")
            page.get_by_label("Buscar na memória").press("Enter")
            _wait(page)
            _screenshot(page, "sotuhire-v0.9-project-evidence.png")
            browser.close()
    finally:
        # Streamlit may finish one final rerun after the browser closes.
        sleep(2)
        _restore_local_state(snapshot)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    args = parser.parse_args()
    capture(args.url)


if __name__ == "__main__":
    main()
