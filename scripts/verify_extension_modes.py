"""Drive the distributed Browser Companion in a real Chromium, in its three ways of running.

    python scripts/verify_extension_modes.py --out report.json [--screenshots DIR] [--modes A,AI,B,C]

A   standalone  : no Local Companion, no Local API, no web app running.
AI  providers   : own Gemini/OpenAI keys against provider fixtures, with negative controls.
B   companion   : Local Companion on 127.0.0.1:8765 over a disposable data dir; web app and Local
                  API off.
C   integrated  : Local Companion + Local API (8787) + production web build (5173), same data dir.

What is real: the ZIP from scripts/package_extension.py, unpacked and loaded with --load-extension;
its MV3 service worker; the action popup (opened with chrome.action.openPopup() on the page in
focus and reached over a CDP connection, since Playwright does not expose action popups as
pages; it has no tab, so the "popup only" guard for keys and pairing applies as for a person);
content-script injection, runtime messaging, chrome.storage, the IndexedDB key vault, the Local
Companion and Local API processes, SQLite on disk.

What is staged, and why:
* pages: a job posting and a repository page are served offline by request interception under
  https://github.com/sotuhire-fixture/... . openPopup() does not grant `activeTab` the way a click
  on the toolbar icon does, so the pages live on a host the extension already holds.
* api.github.com, Gemini and OpenAI answer from fixtures (intercepted in the service worker). The
  provider fixtures reject what the real APIs reject (a bad key; `response_format` on the OpenAI
  Responses API). No real provider call is made: that needs an authorized credential and is
  reported as BLOCKED_EXTERNAL_CREDENTIALS.

Everything runs on fictional data in temporary folders. Exit 1 if any check fails.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from contextlib import ExitStack, contextmanager, suppress
from pathlib import Path

# Service-worker fetches are routed only with this switch (Playwright 1.55).
os.environ.setdefault("PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS", "1")

from playwright.sync_api import BrowserContext, Page, sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
EXTENSION_ID = "joodapjganjanoaaogapmjhcellljnfg"
# Fixture keys, assembled so the file never carries a provider-key shape (scripts/scan_secrets.py).
FAKE_GEMINI_KEY = "AIza" + "FAKE-sotuhire-fixture-key-000000000"
FAKE_OPENAI_KEY = "sk-" + "fake-sotuhire-fixture-key-000000000000"
JOB_URL = "https://github.com/sotuhire-fixture/vaga-ficticia"
REPO_URL = "https://github.com/sotuhire-fixture/projeto-ficticio"
BOOTSTRAP = "ext-modes-disposable-bootstrap-0123456789"
JOB_TITLE = "Pessoa Desenvolvedora Python Pleno"

JOB_PAGE = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Pessoa Desenvolvedora Python Pleno — Empresa Fictícia</title>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"JobPosting",
"title":"Pessoa Desenvolvedora Python Pleno","hiringOrganization":{"@type":"Organization",
"name":"Empresa Fictícia Ltda."},"jobLocation":{"@type":"Place","address":{"addressLocality":
"Recife","addressCountry":"BR"}},"description":"Vaga sintética: APIs com FastAPI, testes com pytest, SQL e revisão de código."}</script></head>
<body><main><h1>Pessoa Desenvolvedora Python Pleno</h1><p>Empresa Fictícia Ltda. · Recife</p>
<section><h2>Requisitos</h2><ul><li>Python e FastAPI</li><li>pytest</li><li>SQL</li></ul>
</section></main></body></html>"""

REPO_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>sotuhire-fixture/projeto-ficticio</title></head><body><main>
<h1>projeto-ficticio</h1><div class="file-navigation">main</div>
<article class="markdown-body" id="readme"><h2>Projeto fictício</h2>
<p>API de exemplo em Python com FastAPI, testes automatizados com pytest e CI.</p></article>
</main></body></html>"""

INSIGHTS = {
    "summary": "Projeto fictício com API Python e testes automatizados.",
    "architecture_assessment": "Camadas simples; evidência limitada ao README e à árvore.",
    "strengths": ["Testes automatizados"],
    "weaknesses": ["Sem documentação de deploy"],
    "inconsistencies": [],
    "priority_recommendations": ["Documentar a execução local"],
    "resume_highlights": ["API em FastAPI com testes"],
    "stack": ["Python", "FastAPI"],
    "evidence": ["README", "tests/"],
    "confidence": "medium",
}


# --------------------------------------------------------------------------- helpers


def port_open(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def wait_http(url: str, timeout: float = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3):  # noqa: S310 - loopback
                return
        except urllib.error.HTTPError:
            return  # it answered
        except Exception:  # noqa: BLE001 - still starting
            time.sleep(0.5)
    raise RuntimeError(f"{url} did not answer in {timeout}s")


@contextmanager
def service(cmd: list[str], env: dict, cwd: Path, health: str, log: Path):
    handle = log.open("w", encoding="utf-8")
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT)
    try:
        wait_http(health)
        yield proc
    finally:
        if os.name == "nt":  # npx starts node as a child; terminate() would leave it serving
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, check=False
            )
        else:
            proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        handle.close()


class Recorder:
    """Every intercepted request the service worker or a page made, for leak checks."""

    def __init__(self) -> None:
        self.requests: list[dict] = []

    def add(self, request) -> None:
        self.requests.append(
            {
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "body": request.post_data or "",
            }
        )


def install_fixtures(context: BrowserContext, recorder: Recorder, github_down: dict) -> None:
    def pages(route):
        recorder.add(route.request)
        url = route.request.url.split("?")[0].rstrip("/")
        body = JOB_PAGE if url == JOB_URL else REPO_PAGE if url == REPO_URL else None
        if body is None:
            return route.fulfill(status=404, body="not found")
        return route.fulfill(status=200, content_type="text/html; charset=utf-8", body=body)

    def github_api(route):
        recorder.add(route.request)
        if github_down["value"]:
            return route.abort("internetdisconnected")
        path = route.request.url.split("api.github.com", 1)[1].split("?")[0]
        base = "/repos/sotuhire-fixture/projeto-ficticio"
        if path == base:
            data: object = {
                "full_name": "sotuhire-fixture/projeto-ficticio",
                "description": "API fictícia em Python",
                "stargazers_count": 3,
                "forks_count": 0,
                "open_issues_count": 1,
                "topics": ["fastapi", "pytest"],
                "license": {"spdx_id": "MIT"},
                "pushed_at": "2026-11-01T10:00:00Z",
                "default_branch": "main",
                "language": "Python",
            }
        elif path == base + "/languages":
            data = {"Python": 12000, "Dockerfile": 300}
        elif path == base + "/commits":
            messages = ["feat: endpoint de saúde", "test: cobre a API", "ci: pytest"]
            data = [
                {"commit": {"message": m, "author": {"date": f"2026-11-0{i}T10:00:00Z"}}}
                for i, m in enumerate(messages, 1)
            ]
        elif path == base + "/readme":
            return route.fulfill(status=200, body="# Projeto fictício\nAPI com FastAPI e pytest.")
        elif path.startswith(base + "/git/trees"):
            files = ("README.md", "pyproject.toml", "app/main.py", "tests/test_api.py")
            data = {"tree": [{"path": p, "type": "blob"} for p in files]}
        else:
            return route.fulfill(status=404, content_type="application/json", body="{}")
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))

    def json_reply(route, status: int, payload: object) -> None:
        route.fulfill(status=status, content_type="application/json", body=json.dumps(payload))

    def gemini(route):
        recorder.add(route.request)
        if route.request.headers.get("x-goog-api-key") != FAKE_GEMINI_KEY:
            return json_reply(route, 400, {"error": {"message": "API key not valid. (fixture)"}})
        if route.request.method == "GET":
            models = [
                {"name": f"models/{m}", "supportedGenerationMethods": ["generateContent"]}
                for m in ("gemini-2.5-flash", "gemini-2.5-pro")
            ]
            return json_reply(route, 200, {"models": models})
        text = json.dumps(INSIGHTS, ensure_ascii=False)
        json_reply(route, 200, {"candidates": [{"content": {"parts": [{"text": text}]}}]})

    def openai(route):
        recorder.add(route.request)
        if route.request.headers.get("authorization") != f"Bearer {FAKE_OPENAI_KEY}":
            return json_reply(
                route, 401, {"error": {"message": "Incorrect API key provided. (fixture)"}}
            )
        if route.request.method == "GET":
            models = [{"id": "gpt-4.1-mini"}, {"id": "gpt-4.1"}, {"id": "whisper-1"}]
            return json_reply(route, 200, {"data": models})
        body = json.loads(route.request.post_data or "{}")
        if "response_format" in body:  # what the real Responses API answers
            return json_reply(
                route,
                400,
                {
                    "error": {
                        "message": "Unsupported parameter: 'response_format'. Use 'text.format'."
                    }
                },
            )
        json_reply(route, 200, {"output_text": json.dumps(INSIGHTS, ensure_ascii=False)})

    context.route("https://github.com/sotuhire-fixture/**", pages)
    context.route("https://api.github.com/**", github_api)
    context.route("https://generativelanguage.googleapis.com/**", gemini)
    context.route("https://api.openai.com/**", openai)


def launch(playwright, profile: Path, unpacked: Path, port: int) -> BrowserContext:
    return playwright.chromium.launch_persistent_context(
        str(profile),
        channel="chromium",
        headless=True,
        viewport={"width": 1280, "height": 900},
        args=[
            f"--disable-extensions-except={unpacked}",
            f"--load-extension={unpacked}",
            f"--remote-debugging-port={port}",
        ],
    )


def worker_of(context: BrowserContext):
    for sw in context.service_workers:
        if EXTENSION_ID in sw.url:
            return sw
    return context.wait_for_event("serviceworker", timeout=20_000)


class Popup:
    """The extension's real action popup, opened on the page in focus."""

    def __init__(self, playwright, context: BrowserContext, port: int, shots: Path | None) -> None:
        self.playwright = playwright
        self.context = context
        self.port = port
        self.cdp = None
        self.shots = shots
        self.errors: list[str] = []
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("popup not open")
        return self._page

    def open(self, target: Page) -> None:
        if self._page is not None and not self._page.is_closed():
            self._page.close()
        target.bring_to_front()
        opened = worker_of(self.context).evaluate(
            "chrome.action.openPopup().then(() => 'opened').catch((e) => 'ERR ' + e.message)"
        )
        if opened != "opened":
            raise RuntimeError(f"openPopup: {opened}")
        self.close()  # a connection sees the targets that exist when it is made
        self.cdp = self.playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{self.port}")
        deadline = time.time() + 15
        while True:
            live = [
                pg
                for c in self.cdp.contexts
                for pg in c.pages
                if pg.url.endswith("/popup.html") and not pg.is_closed()
            ]
            if live:
                self._page = live[-1]
                break
            if time.time() > deadline:
                raise RuntimeError("popup did not appear")
            time.sleep(0.2)
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.page.on(
            "console",
            lambda msg: self.errors.append(msg.text) if msg.type == "error" else None,
        )
        self.page.wait_for_load_state("load")
        self.page.wait_for_function(
            "() => (document.querySelector('#companion-status')?.textContent || '').trim().length > 0",
            timeout=15_000,
        )
        time.sleep(0.6)  # the popup's first status check settles

    def tab(self, name: str) -> None:
        self.page.click(f"[data-tab='{name}']")

    def act(self, action: str, timeout: float = 25) -> dict:
        """Click a popup action and return what the result card says once it settles.

        Like a person: switch to the panel that holds the button and open its <details> first."""
        reveal = (
            "(a) => { const b = document.querySelector(`button[data-action='${a}']`);"
            " const d = b?.closest('details'); if (d) d.open = true;"
            " return b?.closest(\"section[id$='-panel']\")?.id || null; }"
        )
        panel = self.page.evaluate(reveal, action)
        if panel:
            self.tab(panel)
            self.page.evaluate(reveal, action)
        self.page.click(f"button[data-action='{action}']")
        deadline = time.time() + timeout
        text = ""
        while time.time() < deadline:
            if self.page.is_closed():
                return {"text": "(popup closed after opening a tab)", "error": False}
            text = self.page.inner_text("#result")
            if "Processando" not in text and text.strip():
                break
            time.sleep(0.2)
        error = "error" in (self.page.get_attribute("#result", "class") or "")
        return {"text": text.strip(), "error": error}

    def shot(self, name: str) -> None:
        if self.shots:
            self.page.screenshot(path=str(self.shots / f"{name}.png"))

    def storage(self, area: str = "local") -> dict:
        return worker_of(self.context).evaluate(f"chrome.storage.{area}.get(null)")

    def message(self, payload: dict):
        return self.page.evaluate("(m) => chrome.runtime.sendMessage(m)", payload)

    def close(self) -> None:
        if self.cdp is None:
            return
        with suppress(Exception):  # the browser may already be gone
            self.cdp.close()
        self.cdp = None


def check(steps: dict, name: str, ok: bool, **evidence) -> None:
    steps[name] = {"ok": bool(ok), **evidence}


def leak_scan(recorder: Recorder, secrets: list[str], allowed_hosts: dict[str, str]) -> list[str]:
    """Each secret may only travel to its own provider host; nothing may carry cookies."""
    problems = []
    for req in recorder.requests:
        blob = json.dumps(req)
        for secret in secrets:
            if secret in blob and allowed_hosts.get(secret, "") not in req["url"]:
                problems.append(f"{secret[:8]}… sent to {req['url']}")
        headers = {k.lower() for k in req["headers"]}
        if "cookie" in headers and "github.com/sotuhire-fixture" not in req["url"]:
            problems.append(f"cookie sent to {req['url']}")
    return problems


# --------------------------------------------------------------------------- modes


def mode_a(playwright, unpacked: Path, work: Path, shots: Path | None) -> dict:
    steps: dict = {}
    for port in (8765, 8787, 5173):
        check(steps, f"port {port} closed", not port_open(port))
    recorder, github_down = Recorder(), {"value": False}
    context = launch(playwright, work / "profile-a", unpacked, 9341)
    install_fixtures(context, recorder, github_down)
    popup = Popup(playwright, context, 9341, shots)
    try:
        sw = worker_of(context)
        check(steps, "service worker started", sw.url.endswith("/background.js"), url=sw.url)
        manifest = sw.evaluate("chrome.runtime.getManifest()")
        check(
            steps,
            "permissions are the declared minimum",
            sorted(manifest["permissions"]) == ["activeTab", "scripting", "storage"],
            permissions=manifest["permissions"],
            host_permissions=manifest["host_permissions"],
        )
        job = context.new_page()
        job.goto(JOB_URL)
        popup.open(job)
        popup.page.wait_for_function(
            "() => !document.querySelector('#companion-status').textContent.includes('Verificando')",
            timeout=20_000,
        )
        status = popup.page.inner_text("#companion-status")
        check(steps, "popup says it runs standalone", "independente" in status, status=status)
        popup.shot("standalone-popup")

        for name in ("capture-panel", "projects-panel", "ai-panel"):
            popup.tab(name)
            check(steps, f"tab {name} opens", popup.page.is_visible(f"#{name}"))
        ai = popup.message({"type": "SOTUHIRE_AI_STATUS"})
        check(
            steps,
            "works without any AI key",
            not ai["providers"]["gemini"]["configured"]
            and not ai["providers"]["openai"]["configured"],
            default_provider=ai["provider"],
        )

        popup.tab("capture-panel")
        capture = popup.page.evaluate(
            """async () => {
                const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
                await chrome.scripting.executeScript({target: {tabId: tab.id}, files: ['content.js']});
                return chrome.tabs.sendMessage(tab.id, {type: 'SOTUHIRE_CAPTURE'});
            }"""
        )["capture"]
        check(
            steps,
            "assisted capture reads the job in focus (JSON-LD first)",
            capture["job_title"] == JOB_TITLE and "Fictícia" in capture["company"],
            job_title=capture["job_title"],
            company=capture["company"],
        )

        result = popup.act("capture")
        queue = popup.storage().get("pendingCompanionActions", [])
        check(
            steps,
            "a connected action offline is explained and kept in the offline queue",
            result["error"] and "Local Companion offline" in result["text"] and len(queue) == 1,
            message=result["text"][:240],
            queued=len(queue),
        )
        popup.shot("standalone-offline-queue")
        popup.act("capture")
        queue = popup.storage().get("pendingCompanionActions", [])
        check(steps, "the same capture is queued once", len(queue) == 1, queued=len(queue))

        repo = context.new_page()
        repo.goto(REPO_URL)
        popup.open(repo)
        popup.tab("projects-panel")
        default = popup.act("project-standalone", timeout=60)
        check(
            steps,
            "default provider (IA configurada no SotuHire) with nothing running: local report, fallback stated",
            "/100" in default["text"] and "fallback local" in default["text"],
            result=default["text"][:240],
        )
        popup.open(repo)
        popup.tab("ai-panel")
        popup.page.select_option("#ai-provider", "local")
        popup.tab("projects-panel")
        result = popup.act("project-standalone", timeout=30)
        check(
            steps,
            "deterministic project analysis with no service and no key",
            not result["error"] and "/100" in result["text"] and "local-browser" in result["text"],
            result=result["text"][:240],
        )
        popup.shot("standalone-project-analysis")

        repo.bring_to_front()
        button = repo.locator("[data-testid='sotuhire-github-button']")
        button.wait_for(timeout=10_000)
        label = button.inner_text()
        button.click()
        repo.get_by_role("button", name="Analisar com o modelo selecionado").click()
        insight_js = (
            "() => { const root = document.getElementById('sotuhire-github-companion')?.shadowRoot;"
            " const report = root?.querySelector('.report');"
            " return Boolean(report) && !report.className.includes('loading')"
            " && root.textContent.includes('/100'); }"
        )
        repo.wait_for_function(insight_js, timeout=30_000)
        insight = repo.evaluate(
            "document.getElementById('sotuhire-github-companion').shadowRoot"
            ".querySelector('.score')?.textContent"
        )
        check(
            steps,
            "SotuHire Insight button opens a report on the repository",
            "Insight" in label and bool(insight),
            label=label,
            score=insight,
        )
        if shots:
            repo.screenshot(path=str(shots / "github-insight.png"))

        github_down["value"] = True
        popup.open(repo)
        popup.tab("projects-panel")
        result = popup.act("project-standalone", timeout=30)
        check(
            steps,
            "GitHub API unreachable: the analysis still answers from the visible page",
            "/100" in result["text"] or result["error"],
            result=result["text"][:240],
        )
        github_down["value"] = False

        problems = leak_scan(recorder, [], {})
        check(steps, "no cookies sent to public endpoints", not problems, problems=problems)
        unexpected = [
            e
            for e in popup.errors
            if "Failed to fetch" not in e and "ERR_CONNECTION_REFUSED" not in e
        ]
        check(
            steps,
            "popup has no unexpected console errors",
            not unexpected,
            errors=unexpected[:5],
            note="connection refused by the stopped services is expected",
        )
    except Exception as exc:  # noqa: BLE001 - keep the steps already done
        steps["crashed"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:600]}
        if shots:
            for i, pg in enumerate(context.pages):
                with suppress(Exception):
                    pg.screenshot(path=str(shots / f"crash-{i}.png"))
    finally:
        popup.close()
        context.close()
    return steps


def mode_providers(playwright, unpacked: Path, work: Path, shots: Path | None = None) -> dict:
    steps: dict = {}
    recorder, github_down = Recorder(), {"value": False}
    context = launch(playwright, work / "profile-ai", unpacked, 9342)
    install_fixtures(context, recorder, github_down)
    popup = Popup(playwright, context, 9342, None)
    try:
        worker_of(context)
        repo = context.new_page()
        repo.goto(REPO_URL)
        popup.open(repo)

        def save_key(provider: str, key: str, remember: bool) -> dict:
            popup.tab("ai-panel")
            popup.page.select_option("#ai-provider", provider)
            popup.page.fill("#ai-api-key", key)
            popup.page.set_checked("#remember-key", remember)
            return popup.act("save-key")

        def status(provider: str) -> bool:
            return popup.message({"type": "SOTUHIRE_AI_STATUS"})["providers"][provider][
                "configured"
            ]

        def analyze() -> dict:
            popup.tab("projects-panel")
            return popup.act("project-standalone", timeout=40)

        bad = save_key("gemini", "AIza" + "WRONG-key-for-negative-control-000", False)
        check(
            steps,
            "Gemini: a rejected key is not kept (negative control)",
            bad["error"] and not status("gemini"),
            message=bad["text"][:200],
        )
        good = save_key("gemini", FAKE_GEMINI_KEY, False)
        check(
            steps, "Gemini: a valid key lists models", not good["error"], message=good["text"][:200]
        )
        result = analyze()
        check(
            steps,
            "Gemini: the analysis goes through the provider",
            "gemini" in result["text"] and "fallback" not in result["text"],
            result=result["text"][:240],
        )

        bad = save_key("openai", "sk-" + "wrong-negative-control-0000000000", True)
        check(
            steps,
            "OpenAI: a rejected key is not kept (negative control)",
            bad["error"] and not status("openai"),
            message=bad["text"][:200],
        )
        good = save_key("openai", FAKE_OPENAI_KEY, True)
        check(
            steps, "OpenAI: a valid key lists models", not good["error"], message=good["text"][:200]
        )
        result = analyze()
        check(
            steps,
            "OpenAI: the analysis goes through the Responses API (fixture rejects response_format)",
            "openai" in result["text"] and "fallback" not in result["text"],
            result=result["text"][:240],
        )

        local = popup.storage("local")
        session = popup.storage("session")
        check(
            steps,
            "keys never in chrome.storage.local; the session key only in session storage",
            FAKE_GEMINI_KEY not in json.dumps(local)
            and FAKE_OPENAI_KEY not in json.dumps(local)
            and FAKE_GEMINI_KEY in json.dumps(session)
            and FAKE_OPENAI_KEY not in json.dumps(session),
            local_keys=sorted(local),
            note="the remembered OpenAI key lives in the extension's IndexedDB vault",
        )
        problems = leak_scan(
            recorder,
            [FAKE_GEMINI_KEY, FAKE_OPENAI_KEY],
            {
                FAKE_GEMINI_KEY: "generativelanguage.googleapis.com",
                FAKE_OPENAI_KEY: "api.openai.com",
            },
        )
        check(steps, "each key travels only to its own provider", not problems, problems=problems)

        repo.bring_to_front()
        answer = repo.evaluate(
            """() => new Promise((resolve) => {
                try {
                  chrome.runtime.sendMessage(EXTENSION_ID_VALUE, {type: 'SOTUHIRE_AI_SAVE_KEY'}, (r) => resolve(r || 'no answer'));
                } catch (e) { resolve('no access: ' + e.message); }
            })""".replace("EXTENSION_ID_VALUE", json.dumps(EXTENSION_ID))
        )
        check(
            steps,
            "a web page cannot message the extension",
            not (isinstance(answer, dict) and answer.get("ok")),
            answer=str(answer)[:200],
        )
        popup.open(repo)
        popup.tab("ai-panel")
        popup.page.select_option("#ai-provider", "openai")
        popup.act("remove-key")
        check(steps, "removing a key clears it", not status("openai"))
    except Exception as exc:  # noqa: BLE001 - keep the steps already done
        steps["crashed"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:600]}
        if shots:
            for i, pg in enumerate(context.pages):
                with suppress(Exception):
                    pg.screenshot(path=str(shots / f"crash-{i}.png"))
    finally:
        popup.close()
        context.close()
    steps["real provider call"] = {
        "ok": True,
        "status": "BLOCKED_EXTERNAL_CREDENTIALS",
        "note": "no authorized Gemini/OpenAI credential; fixtures only",
    }
    return steps


def service_env(data_dir: Path, **extra: str) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("SOTUHIRE_")}
    env["SOTUHIRE_DATA_DIR"] = str(data_dir)
    env["PYTHONPATH"] = str(ROOT)
    env.update(extra)
    return env


COMPANION = [sys.executable, "-m", "modules.local_api.server"]
COMPANION_HEALTH = "http://127.0.0.1:8765/health"


def mode_b(playwright, unpacked: Path, work: Path, shots: Path | None) -> dict:
    steps: dict = {}
    data = work / "data-b"
    data.mkdir()
    env = service_env(data)
    recorder, github_down = Recorder(), {"value": False}
    profile = work / "profile-b"
    for port in (8787, 5173):
        check(steps, f"port {port} closed (web app and Local API off)", not port_open(port))
    context = launch(playwright, profile, unpacked, 9343)
    install_fixtures(context, recorder, github_down)
    popup = Popup(playwright, context, 9343, shots)
    try:
        worker_of(context)
        job = context.new_page()
        job.goto(JOB_URL)
        popup.open(job)
        popup.act("capture")
        queued = len(popup.storage().get("pendingCompanionActions", []))
        check(steps, "capture queued while the Companion is off", queued == 1, queued=queued)

        with service(COMPANION, env, ROOT, COMPANION_HEALTH, work / "companion-b.log"):
            popup.open(job)
            status = popup.page.inner_text("#companion-status")
            check(steps, "Companion online asks for pairing", "pareamento" in status, status=status)
            paired = popup.act("pair-companion")
            compat = popup.page.inner_text("#compatibility-status")
            check(
                steps,
                "pairing and version handshake",
                "pareada" in paired["text"] and "compatível" in compat,
                handshake=compat,
            )
            popup.shot("companion-paired")
            retried = popup.act("retry-pending")
            left = len(popup.storage().get("pendingCompanionActions", []))
            check(
                steps,
                "the offline queue is delivered after pairing",
                left == 0 and "1 pendência(s) enviada(s)" in retried["text"],
                result=retried["text"][:200],
            )
            first = popup.act("capture")
            second = popup.act("capture")
            check(
                steps,
                "capture saved; repeating it is accepted without a second record",
                not first["error"] and not second["error"],
                first=first["text"][:200],
                second=second["text"][:200],
            )
            tracker = popup.act("tracker")
            again = popup.act("tracker")
            check(
                steps,
                "job sent to the Tracker; sending it again does not fail",
                not tracker["error"] and not again["error"],
                first=tracker["text"][:200],
                second=again["text"][:200],
            )
            exam = popup.act("capture-public-exam")
            check(
                steps,
                "public exam (edital) captured as a snapshot",
                not exam["error"],
                result=exam["text"][:200],
            )
            analyzed = popup.act("analyze", timeout=40)
            check(
                steps,
                "Match/ATS computed by the Companion",
                not analyzed["error"] and "Match" in analyzed["text"],
                result=analyzed["text"][:240],
            )
            worker_of(context).evaluate(
                "chrome.storage.session.set({companionSessionExpiresAt: Date.now() - 1000})"
            )
            expired = popup.act("capture")
            check(
                steps,
                "an expired session is refused and the capture is kept",
                expired["error"] and "Pareie" in expired["text"],
                result=expired["text"][:240],
            )
            popup.act("pair-companion")
            renewed = popup.act("retry-pending")
            check(
                steps,
                "re-pairing renews the session and flushes the queue",
                "enviada" in renewed["text"],
                result=renewed["text"][:200],
            )
        check(
            steps,
            "nothing asked of the web app (5173) or the Local API (8787)",
            not any(":5173" in r["url"] or ":8787" in r["url"] for r in recorder.requests),
        )
    except Exception as exc:  # noqa: BLE001 - keep the steps already done
        steps["crashed"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:600]}
        if shots:
            for i, pg in enumerate(context.pages):
                with suppress(Exception):
                    pg.screenshot(path=str(shots / f"crash-{i}.png"))
    finally:
        popup.close()
        context.close()

    context = launch(playwright, profile, unpacked, 9344)
    try:
        worker_of(context)
        session = worker_of(context).evaluate("chrome.storage.session.get(null)")
        local = worker_of(context).evaluate("chrome.storage.local.get(null)")
        check(
            steps,
            "after a browser restart the session is gone (re-pair required), settings remain",
            "companionSessionToken" not in session and "aiProvider" in local,
        )
    finally:
        context.close()
    with service(COMPANION, env, ROOT, COMPANION_HEALTH, work / "companion-b2.log"):
        pass
    db = data / "sotuhire.db"
    check(
        steps,
        "data written only to the disposable data dir",
        db.exists(),
        files=len(list(data.rglob("*"))),
    )
    return steps


def mode_c(playwright, unpacked: Path, work: Path, shots: Path | None) -> dict:
    steps: dict = {}
    data = work / "data-c"
    data.mkdir()
    env = service_env(data)
    api_env = service_env(data, SOTUHIRE_PAIRING_BOOTSTRAP=BOOTSTRAP)
    recorder, github_down = Recorder(), {"value": False}
    npx = shutil.which("npx") or "npx"
    preview = [npx, "vite", "preview", "--port", "5173", "--strictPort", "--host", "127.0.0.1"]
    with ExitStack() as stack:
        stack.enter_context(
            service(COMPANION, env, ROOT, COMPANION_HEALTH, work / "companion-c.log")
        )
        stack.enter_context(
            service(
                [sys.executable, "scripts/run_api.py"],
                api_env,
                ROOT,
                "http://127.0.0.1:8787/api/v1/health",
                work / "api-c.log",
            )
        )
        stack.enter_context(
            service(preview, env, WEB, "http://127.0.0.1:5173/", work / "web-c.log")
        )
        context = launch(playwright, work / "profile-c", unpacked, 9345)
        install_fixtures(context, recorder, github_down)
        popup = Popup(playwright, context, 9345, shots)
        try:
            worker_of(context)
            app = context.new_page()
            app.add_init_script("localStorage.setItem('sotuhire.api-mode', 'real')")
            app.goto(f"http://127.0.0.1:5173/dashboard#sotuhire-pairing={BOOTSTRAP}")
            app.wait_for_function(
                "() => document.body.innerText.includes('API local conectada')", timeout=45_000
            )
            check(steps, "web app paired with the Local API", True)

            job = context.new_page()
            job.goto(JOB_URL)
            popup.open(job)
            popup.act("pair-companion")
            popup.open(job)
            prepared = popup.act("prepare-application", timeout=30)
            time.sleep(1.5)
            lab = next((p for p in context.pages if "/application-lab" in p.url), None)
            lab_url = lab.url if lab else ""
            check(
                steps,
                "Prepare application opens the Lab with identifiers only",
                bool(lab)
                and "capture_id=" in lab_url
                and "job_snapshot_id=" in lab_url
                and "Python" not in lab_url,
                popup=prepared["text"][:160],
                lab_url=lab_url.split("?")[0],
            )
            if lab:
                lab.wait_for_load_state("networkidle")
                body = lab.inner_text("body")
                snapshot = lab_url.split("job_snapshot_id=", 1)[1].split("&", 1)[0]
                check(
                    steps,
                    "the Lab receives the captured job snapshot, ready",
                    snapshot[:12] in lab.content() and "PRONTO" in body.upper(),
                    note="the card shows the snapshot id, not the job title (UX issue recorded)",
                )
                if shots:
                    lab.screenshot(path=str(shots / "integrated-application-lab.png"))

            popup.open(job)
            first = popup.act("tracker")
            second = popup.act("tracker")
            app.goto("http://127.0.0.1:5173/tracker")
            app.wait_for_load_state("networkidle")
            cards = app.locator("[data-testid='kanban-card']", has_text=JOB_TITLE)
            cards.first.wait_for(timeout=15_000)
            check(
                steps,
                "the job reaches the web app Tracker once, though sent twice",
                cards.count() == 1,
                cards=cards.count(),
                first=first["text"][:160],
                second=second["text"][:160],
            )

            repo = context.new_page()
            repo.goto(REPO_URL)
            popup.open(repo)
            popup.tab("projects-panel")
            sent = popup.act("project-profile", timeout=30)
            check(
                steps,
                "project evidence sent for Profile review",
                not sent["error"],
                result=sent["text"][:200],
            )

            popup.open(repo)
            popup.tab("ai-panel")
            popup.page.select_option("#ai-provider", "sotuhire")
            popup.tab("projects-panel")
            via = popup.act("project-standalone", timeout=40)
            check(
                steps,
                "'IA configurada no SotuHire' answers and says which path it took",
                not via["error"] and "/100" in via["text"],
                result=via["text"][:240],
            )
        finally:
            popup.close()
            context.close()

    context = launch(playwright, work / "profile-c", unpacked, 9346)
    try:
        worker_of(context)
        local = worker_of(context).evaluate("chrome.storage.local.get(null)")
        check(
            steps,
            "after a browser restart nothing is left pending",
            not local.get("pendingCompanionActions"),
            pending=len(local.get("pendingCompanionActions") or []),
        )
    finally:
        context.close()
    return steps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--modes", default="A,AI,B,C")
    args = parser.parse_args()
    modes = set(args.modes.split(","))
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    report: dict = {"extension_id": EXTENSION_ID, "modes": {}}
    with tempfile.TemporaryDirectory(
        prefix="sotuhire-ext-modes-", ignore_cleanup_errors=True
    ) as tmp:
        work = Path(tmp)
        archive = args.zip or work / "extension.zip"
        if not args.zip:
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "package_extension.py"),
                    "--output",
                    str(archive),
                ],
                check=True,
                capture_output=True,
            )
        report["zip"] = archive.name
        unpacked_root = work / "unpacked"
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(unpacked_root)
        unpacked = next(p.parent for p in unpacked_root.rglob("manifest.json"))
        manifest = json.loads((unpacked / "manifest.json").read_text(encoding="utf-8"))
        report["version"] = manifest["version"]
        with sync_playwright() as playwright:
            runners = {
                "A": lambda: mode_a(playwright, unpacked, work, args.screenshots),
                "AI": lambda: mode_providers(playwright, unpacked, work),
                "B": lambda: mode_b(playwright, unpacked, work, args.screenshots),
                "C": lambda: mode_c(playwright, unpacked, work, args.screenshots),
            }
            for name, run in runners.items():
                if name not in modes:
                    continue
                try:
                    report["modes"][name] = run()
                except Exception as exc:  # noqa: BLE001 - reported, then exit 1
                    message = f"{type(exc).__name__}: {exc}"[:800]
                    report["modes"][name] = {"crashed": {"ok": False, "error": message}}
    failed = [
        f"{mode}: {step}"
        for mode, steps in report["modes"].items()
        for step, result in steps.items()
        if not result.get("ok")
    ]
    report["ok"] = not failed
    report["failed"] = failed
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "failed": failed}, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
