"""Capture the fictional SotuHire v2 product gallery and release GIF."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from PIL import Image
from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "apps" / "web"
OUTPUT_DIR = ROOT / "docs" / "assets" / "screenshots" / "v2"
GIF_TARGET = (
    ROOT / "docs" / "assets" / "screenshots" / "sotuhire-v2-human-approved-career-copilot.gif"
)
DEFAULT_URL = "http://127.0.0.1:5173"

SHOTS = (
    ("/dashboard", "01-cockpit-light.png"),
    ("/dashboard", "02-cockpit-dark.png"),
    ("/dashboard", "03-copilot.png"),
    ("/approvals", "04-approval-queue.png"),
    ("/evidence", "05-evidence-inbox.png"),
    ("/evidence", "06-evidence-graph.png"),
    ("/profile", "07-profile.png"),
    ("/portfolio", "08-portfolio.png"),
    ("/resume-studio", "09-resume-studio.png"),
    ("/job", "10-opportunity.png"),
    ("/application-lab", "11-application-lab.png"),
    ("/tracker", "12-tracker.png"),
    ("/interviews", "13-interview.png"),
    ("/career", "14-career-plan.png"),
    ("/intelligence", "15-analytics.png"),
    ("/settings", "16-ai-settings.png"),
    ("/privacy", "17-privacy.png"),
    ("/sources", "18-extension.png"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()
    server = None
    if not _is_up(args.url):
        server = _start_server(args.url)
        _wait(args.url)
    try:
        capture(args.url)
    finally:
        if server is not None:
            _stop(server)


def capture(base_url: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for route, filename in SHOTS:
            page = _page(browser, 1440, 1000)
            theme = "dark" if filename == "02-cockpit-dark.png" else "light"
            locale = (
                "en-US" if filename in {"06-evidence-graph.png", "15-analytics.png"} else "pt-BR"
            )
            _preferences(page, locale, theme)
            page.goto(base_url + route, wait_until="networkidle")
            page.wait_for_timeout(350)
            if filename == "03-copilot.png":
                page.get_by_role("button", name="Abrir Copilot contextual").click()
                page.wait_for_timeout(250)
            target = OUTPUT_DIR / filename
            page.screenshot(path=str(target), full_page=False)
            if filename in {
                "01-cockpit-light.png",
                "03-copilot.png",
                "04-approval-queue.png",
                "05-evidence-inbox.png",
                "08-portfolio.png",
                "11-application-lab.png",
                "12-tracker.png",
                "13-interview.png",
            }:
                frames.append(target)
            page.close()
        mobile = _page(browser, 360, 800)
        _preferences(mobile, "pt-BR", "light")
        mobile.goto(base_url + "/dashboard", wait_until="networkidle")
        mobile.screenshot(path=str(OUTPUT_DIR / "19-mobile-cockpit.png"), full_page=False)
        mobile.get_by_role("button", name="Abrir Copilot contextual").click()
        mobile.screenshot(path=str(OUTPUT_DIR / "20-mobile-copilot.png"), full_page=False)
        browser.close()
    _gif(frames)


def _page(browser: Browser, width: int, height: int) -> Page:
    return browser.new_page(viewport={"width": width, "height": height})


def _preferences(page: Page, locale: str, theme: str) -> None:
    preferences = json.dumps({"locale": locale, "theme": theme})
    page.add_init_script(
        f"""localStorage.setItem('sotuhire.onboarding.v1.complete', 'true');
        localStorage.setItem('sotuhire.api-mode', 'demo');
        localStorage.setItem('sotuhire.ui-preferences.v1', JSON.stringify({preferences}));"""
    )


def _gif(paths: list[Path]) -> None:
    frames: list[Image.Image] = []
    for path in paths:
        with Image.open(path) as image:
            frame = image.convert("RGB").resize((960, 667), Image.Resampling.LANCZOS)
            frames.append(frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    first, *rest = frames
    first.save(
        GIF_TARGET,
        save_all=True,
        append_images=rest,
        duration=1200,
        loop=0,
        optimize=True,
        disposal=2,
    )
    for frame in frames:
        frame.close()


def _start_server(url: str) -> subprocess.Popen[bytes]:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        raise RuntimeError("npm not found")
    parsed = urlparse(url)
    return subprocess.Popen(
        [
            npm,
            "run",
            "dev",
            "--",
            "--host",
            parsed.hostname or "127.0.0.1",
            "--port",
            str(parsed.port or 5173),
        ],
        cwd=WEB_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _wait(url: str) -> None:
    deadline = time.time() + 120
    while time.time() < deadline:
        if _is_up(url):
            return
        time.sleep(0.5)
    raise RuntimeError("frontend did not start")


def _stop(server: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(server.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        server.terminate()


def _is_up(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            return response.status < 500
    except (OSError, URLError):
        return False


if __name__ == "__main__":
    main()
