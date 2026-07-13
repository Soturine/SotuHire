"""Capture deterministic Browser Companion popup states without personal data."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
POPUP = ROOT / "browser-extension" / "popup.html"
OUTPUT = ROOT / "docs" / "assets" / "screenshots" / "extension"

CHROME_STUB = r"""
(() => {
  const values = {};
  const capture = {
    kind: "job",
    page_title: "Analista de Dados — oportunidade fictícia",
    url: "https://example.invalid/jobs/analista-dados",
    domain: "example.invalid",
    visible_text: "Vaga fictícia: Python, SQL, relatórios e comunicação.",
    job_title: "Analista de Dados",
    company: "Empresa Exemplo",
    location: "Remoto",
    description: "Python, SQL, relatórios e comunicação.",
    extraction_strategy: "schema_org_jobposting",
    structured_data: {
      "@type": "JobPosting",
      title: "Analista de Dados",
      hiringOrganization: { name: "Empresa Exemplo" }
    },
    captured_at: "2026-07-11T12:00:00Z",
    collection_method: "browser_assisted_capture"
  };
  const project = {
    url: "https://github.com/example/fictitious-api-lab",
    owner: "example",
    repo: "fictitious-api-lab",
    title: "fictitious-api-lab",
    page_type: "github_repo",
    visible_text: "API pública fictícia com testes.",
    readme_text: "FastAPI, SQL e Pytest.",
    files_sampled: ["README.md", "src/app.py", "tests/test_app.py"],
    commit_messages: ["feat: add API", "test: cover endpoints"],
    languages: ["Python"],
    topics: ["fastapi"],
    analysis_result: {},
    provider_used: "local"
  };
  globalThis.chrome = {
    storage: { local: {
      get(keys, callback) {
        const result = Object.fromEntries((keys || Object.keys(values)).map((key) => [key, values[key]]));
        if (callback) callback(result);
        return Promise.resolve(result);
      },
      set(payload) { Object.assign(values, payload); return Promise.resolve(); },
      remove(keys) { for (const key of keys) delete values[key]; return Promise.resolve(); }
    }, session: {
      get: async () => ({}), set: async () => {}, remove: async () => {}
    }},
    runtime: {
      getManifest: () => ({ version: "0.9.2" }),
      sendMessage: async (message) => {
        if (message.type === "SOTUHIRE_AI_STATUS") return {
          ok: true,
          provider: "sotuhire",
          models: { sotuhire: "configurado-no-sotuhire" },
          providers: {
            gemini: { configured: false, persistent: false },
            openai: { configured: false, persistent: false }
          }
        };
        if (message.type === "SOTUHIRE_AI_LIST_MODELS") return {
          ok: true,
          models: message.provider === "gemini"
            ? ["gemini-2.5-flash", "gemini-2.5-pro"]
            : message.provider === "openai"
              ? ["gpt-4.1-mini", "gpt-4.1"]
              : [message.provider === "local" ? "local-browser" : "configurado-no-sotuhire"],
          source: ["gemini", "openai"].includes(message.provider) ? "builtin" : "local",
          refreshedAt: "",
          warning: ["gemini", "openai"].includes(message.provider)
            ? "Configure uma chave própria para consultar o catálogo oficial."
            : ""
        };
        if (message.type === "SOTUHIRE_AI_ANALYZE") return {
          ok: true,
          project,
          report: {
            overall_score: 84, grade: "B", summary: "Projeto público bem estruturado, com testes e documentação verificáveis.",
            stack: ["Python", "FastAPI", "Pytest"], provider_used: "local-browser", model_used: "local-browser",
            fallback_used: false, documentation_score: 82, commit_quality_score: 78,
            architecture_signal_score: 86, technical_depth_score: 81, recruiter_readiness_score: 84,
            commit_analysis: { maintenance_signal_score: 80 }, strengths: ["Estrutura modular e testes públicos."],
            weaknesses: ["Pode documentar melhor decisões arquiteturais."], inconsistencies: [],
            priority_recommendations: ["Adicionar ADRs curtos para decisões centrais."],
            resume_highlights: ["Desenvolveu API FastAPI com testes automatizados."],
            prompt_id: "extension_github_portfolio_analysis_v2", prompt_version: "2.0.0"
          }
        };
        return { ok: true };
      }
    },
    tabs: {
      query: async () => [{ id: 1 }],
      sendMessage: async (_id, message) => {
        if (message.type === "SOTUHIRE_PROJECT") return { project };
        if (message.type === "SOTUHIRE_APPLICATIONS") return { applications: [capture] };
        return { capture };
      }
    },
    scripting: { executeScript: async () => [] }
  };
  globalThis.__companionOffline = false;
  globalThis.fetch = async (url) => {
    if (globalThis.__companionOffline) throw new Error("offline demo");
    const path = String(url);
    let payload = { ok: true, message: "Ação concluída no Companion local." };
    if (path.endsWith("/health")) payload = { ok: true, message: "SotuHire Local Companion conectado." };
    if (path.endsWith("/handshake")) payload = {
      extension_version: "0.9.2",
      companion_version: "1.9.6",
      api_version: "v1",
      app_version: "1.9.6",
      capabilities: [
        "capture.job", "capture.public_exam", "capture.github", "capture.snapshot",
        "queue.retry", "queue.export_import", "jobposting.jsonld", "ai.own_key"
      ],
      compatible: true,
      warnings: [],
      min_supported_extension_version: "0.9.1",
      max_tested_extension_version: "0.9.2",
      min_supported_companion_version: "1.9.5"
    };
    if (path.includes("context-summary")) payload = {
      ok: true,
      app_version: "1.9.6",
      profile_available: true,
      profile_summary: "Resumo seguro disponível no backend local.",
      enabled_flows: ["job", "public_exam", "github", "profile_evidence"],
      ai_provider_status: "local",
      warnings: ["Nenhum dado sensível foi enviado."]
    };
    if (path.includes("public-exam")) payload = {
      ok: true,
      message: "Edital fictício capturado para revisão.",
      snapshot_id: "public-exam-snapshot-demo"
    };
    if (path.includes("/capture/job")) payload = {
      ok: true,
      message: "Vaga fictícia capturada localmente com snapshot imutável.",
      snapshot_id: "job-snapshot-demo"
    };
    return { ok: true, status: 200, json: async () => payload };
  };
  Object.defineProperty(navigator, "clipboard", { value: { writeText: async () => {} } });
})();
"""


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--allow-file-access-from-files"],
        )
        page = browser.new_page(viewport={"width": 430, "height": 980}, device_scale_factor=1)
        page.add_init_script(CHROME_STUB)
        page.goto(POPUP.as_uri(), wait_until="load")
        page.wait_for_timeout(400)
        _shot(page, "popup-main.png")
        _action(page, "health", "status-connected.png")
        _action(page, "capture", "capture-job.png")
        _action(page, "capture-public-exam", "capture-public-exam.png")
        _tab(page, "projects-panel")
        _action(page, "project-standalone", "capture-github.png")
        _tab(page, "capture-panel")
        page.locator("details").first.evaluate("element => element.open = true")
        _action(page, "collect-page", "applications-batch.png")
        _tab(page, "ai-panel")
        page.locator("#ai-provider").select_option("gemini")
        page.wait_for_timeout(250)
        page.locator("button[data-action='refresh-models']").click()
        page.wait_for_timeout(250)
        _shot(page, "ai-provider-setup.png")
        _shot(page, "ai-provider-gemini.png")
        page.locator("#ai-provider").select_option("openai")
        page.wait_for_timeout(250)
        page.locator("button[data-action='refresh-models']").click()
        page.wait_for_timeout(250)
        _shot(page, "ai-provider-openai.png")
        page.locator("#ai-provider").select_option("sotuhire")
        page.locator("#ai-panel details").evaluate("element => element.open = true")
        _action(page, "context-summary", "safe-context.png")
        page.locator("button[data-action='compatibility']:visible").click()
        page.wait_for_timeout(250)
        _shot(page, "compatibility-diagnostic.png")
        _tab(page, "capture-panel")
        page.evaluate("globalThis.__companionOffline = true")
        _action(page, "capture", "companion-offline.png")
        page.locator("#capture-panel details").evaluate("element => element.open = true")
        page.locator("button[data-action='retry-pending']:visible").click()
        page.wait_for_timeout(250)
        _shot(page, "queue-offline.png")
        _capture_github_modal(browser)
        browser.close()


def _action(page: Page, action: str, filename: str) -> None:
    page.locator(f"button[data-action='{action}']:visible").first.click()
    page.wait_for_timeout(250)
    _shot(page, filename)


def _shot(page: Page, filename: str) -> None:
    page.screenshot(path=str(OUTPUT / filename), full_page=True)


def _tab(page: Page, panel: str) -> None:
    page.locator(f"button[data-tab='{panel}']").click()
    page.wait_for_timeout(150)


def _capture_github_modal(browser: Browser) -> None:
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page.add_init_script(CHROME_STUB)
    page.route(
        "https://github.com/**",
        lambda route: route.fulfill(
            content_type="text/html",
            body="""
            <style>
              body{margin:0;background:#0d1117;color:#e6edf3;font:14px system-ui}
              header{height:64px;background:#010409;border-bottom:1px solid #30363d}
              main{max-width:1180px;margin:auto;padding:32px}.file-navigation{display:flex;justify-content:flex-end}
              .repo{border:1px solid #30363d;border-radius:10px;padding:22px;margin-top:20px;background:#161b22}
              .markdown-body{margin-top:25px;padding:24px;border-top:1px solid #30363d;line-height:1.6}
            </style>
            <header></header><main><h1>example / fictitious-api-lab</h1><div class="file-navigation"></div>
            <div class="repo"><a title="src/app.py" href="/example/fictitious-api-lab/blob/main/src/app.py">src/app.py</a>
            <a title="tests/test_app.py" href="/example/fictitious-api-lab/blob/main/tests/test_app.py">tests/test_app.py</a>
            <a href="/example/fictitious-api-lab/commit/123" data-testid="commit-row-item">feat: add API validation</a>
            <article id="readme" class="markdown-body"><h2>Fictitious API Lab</h2><p>FastAPI pública fictícia com testes Pytest, documentação e CI.</p></article></div></main>
            """,
        ),
    )
    page.goto("https://github.com/example/fictitious-api-lab", wait_until="load")
    page.add_script_tag(path=str(ROOT / "browser-extension" / "project_analysis.js"))
    page.add_script_tag(path=str(ROOT / "browser-extension" / "github_injected.js"))
    page.locator("[data-testid='sotuhire-github-button']").click()
    page.locator("button[data-action='analyze']").click()
    page.locator(".report .hero").wait_for(timeout=5_000)
    page.screenshot(path=str(OUTPUT / "github-analysis-modal.png"), full_page=False)
    page.close()


if __name__ == "__main__":
    main()
