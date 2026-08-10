"""Capture the fictional v1.10.1 career-intelligence gallery and walkthrough."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from PIL import Image
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "apps" / "web"
OUTPUT_DIR = ROOT / "docs" / "assets" / "screenshots"
DEFAULT_URL = "http://127.0.0.1:5173"
GIF_TARGET = OUTPUT_DIR / "sotuhire-v1.10.1-career-intelligence-walkthrough.gif"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--no-server", action="store_true")
    args = parser.parse_args()
    server = None
    if not args.no_server and not _is_up(args.url):
        server = _start_server(args.url)
        _wait(args.url)
    try:
        capture(args.url)
    finally:
        if server is not None:
            _stop_server(server)


def capture(base_url: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.add_init_script(
            """
            localStorage.setItem('sotuhire.onboarding.v1.complete', 'true');
            localStorage.setItem('sotuhire.api-mode', 'demo');
            if (!localStorage.getItem('sotuhire.ui-preferences.v1')) {
              localStorage.setItem('sotuhire.ui-preferences.v1', JSON.stringify({locale:'pt-BR',theme:'light'}));
            }
            """
        )

        _shot(page, base_url, "/dashboard", "sotuhire-v1.10.1-home-light-pt.png", frames)
        page.evaluate(
            "localStorage.setItem('sotuhire.ui-preferences.v1', JSON.stringify({locale:'en-US',theme:'dark'}))"
        )
        _shot(page, base_url, "/dashboard", "sotuhire-v1.10.1-home-dark-en.png", frames)
        page.evaluate(
            "localStorage.setItem('sotuhire.ui-preferences.v1', JSON.stringify({locale:'pt-BR',theme:'light'}))"
        )
        _shot(page, base_url, "/radar", "sotuhire-v1.10.1-radar-official-sources.png", frames)
        _shot(page, base_url, "/interviews", "sotuhire-v1.10.1-interview-star-followup.png", frames)
        page.get_by_role("button", name="Abrir ajuda desta página").click()
        page.wait_for_timeout(250)
        _save(page, "sotuhire-v1.10.1-help-drawer.png", frames)
        _shot(page, base_url, "/career", "sotuhire-v1.10.1-career-actions-plan.png", frames)
        _shot(page, base_url, "/settings", "sotuhire-v1.10.1-settings-theme-locale.png", frames)

        page.set_viewport_size({"width": 390, "height": 844})
        _shot(page, base_url, "/interviews", "sotuhire-v1.10.1-mobile-interviews.png", frames)
        browser.close()
    _gif(frames)


def _shot(page: Page, base_url: str, route: str, name: str, frames: list[Path]) -> None:
    page.goto(f"{base_url}{route}", wait_until="networkidle")
    page.add_style_tag(
        content="*,*::before,*::after{animation-duration:0s!important;transition-duration:0s!important}"
    )
    page.wait_for_timeout(350)
    _save(page, name, frames)


def _save(page: Page, name: str, frames: list[Path]) -> None:
    target = OUTPUT_DIR / name
    page.screenshot(path=str(target), full_page=False)
    frames.append(target)


def _gif(paths: list[Path]) -> None:
    frames: list[Image.Image] = []
    for path in paths:
        with Image.open(path) as image:
            resized = image.convert("RGB").resize((960, 667), Image.Resampling.LANCZOS)
            frames.append(resized.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    first, *rest = frames
    first.save(
        GIF_TARGET,
        save_all=True,
        append_images=rest,
        duration=1400,
        loop=0,
        optimize=True,
        disposal=2,
    )
    for frame in frames:
        frame.close()


def _start_server(url: str) -> subprocess.Popen[bytes]:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm was not found in PATH")
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
    raise RuntimeError(f"Frontend did not start at {url}")


def _stop_server(server: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(server.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
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
