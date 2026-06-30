"""Capture the modern web product walkthrough screenshots and GIF."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from PIL import Image
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "apps" / "web"
OUTPUT_DIR = ROOT / "docs" / "assets" / "screenshots"
DEFAULT_URL = "http://127.0.0.1:5173"


@dataclass(frozen=True)
class Shot:
    path: str
    label: str
    file: str | None = None
    selector: str | None = None


WALKTHROUGH = [
    Shot("/dashboard", "Dashboard", "sotuhire-web-dashboard.png"),
    Shot("/profile", "Perfil", "sotuhire-web-profile.png"),
    Shot("/resume", "Curriculo"),
    Shot("/job", "Vaga"),
    Shot("/match", "Match", "sotuhire-web-match.png"),
    Shot("/ats", "ATS"),
    Shot("/tailor", "Tailor"),
    Shot("/github", "GitHub/Portfolio"),
    Shot("/sources", "Fontes e Captura", "sotuhire-web-sources.png", "#opportunity-inbox"),
    Shot(
        "/sources",
        "Extensao Local e Perfil",
        "sotuhire-web-extension-profile-candidates.png",
        "#local-extension",
    ),
    Shot("/radar", "Radar"),
    Shot("/radar", "Wishlist IA/local", selector="#radar-ai-wishlist"),
    Shot("/radar", "Agendamentos", "sotuhire-web-radar-schedules.png", "#radar-schedules"),
    Shot("/radar", "Notificacoes", "sotuhire-web-notifications.png", "#radar-notifications"),
    Shot("/tracker", "Kanban/Tracker", "sotuhire-web-tracker.png"),
    Shot("/settings", "Configuracoes IA", "sotuhire-web-settings-ai.png"),
]
GIF_FILE = "sotuhire-web-product-walkthrough.gif"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--no-server", action="store_true")
    args = parser.parse_args()

    server = None
    if not args.no_server and not _is_up(args.url):
        server = _start_dev_server()
        _wait_until_up(args.url)
    try:
        capture(args.url)
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=8)
            except subprocess.TimeoutExpired:
                server.kill()


def capture(base_url: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame_paths: list[Path] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        for index, shot in enumerate(WALKTHROUGH, start=1):
            page.goto(f"{base_url}{shot.path}", wait_until="networkidle")
            _prepare(page, shot)
            frame = OUTPUT_DIR / f".web-walkthrough-frame-{index:02d}.png"
            page.screenshot(path=str(frame), full_page=False)
            frame_paths.append(frame)
            if shot.file:
                page.screenshot(path=str(OUTPUT_DIR / shot.file), full_page=False)
        browser.close()
    _write_gif(frame_paths, OUTPUT_DIR / GIF_FILE)
    for frame in frame_paths:
        frame.unlink(missing_ok=True)


def _prepare(page: Page, shot: Shot) -> None:
    page.wait_for_timeout(800)
    if shot.selector:
        page.locator(shot.selector).scroll_into_view_if_needed()
        page.wait_for_timeout(500)
    if shot.file == "sotuhire-web-extension-profile-candidates.png":
        button = page.locator("[data-testid='view-extension-profile-candidates']").first
        button.click()
        page.locator("[data-testid='extension-profile-candidates']").wait_for(timeout=5_000)
        page.wait_for_timeout(500)


def _write_gif(frame_paths: list[Path], target: Path) -> None:
    frames = [Image.open(path).convert("P", palette=Image.Palette.ADAPTIVE) for path in frame_paths]
    first, *rest = frames
    first.save(
        target,
        save_all=True,
        append_images=rest,
        duration=1150,
        loop=0,
        optimize=True,
    )
    for frame in frames:
        frame.close()


def _start_dev_server() -> subprocess.Popen:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm was not found in PATH")
    return subprocess.Popen(
        [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        cwd=WEB_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _wait_until_up(url: str) -> None:
    deadline = time.time() + 120
    while time.time() < deadline:
        if _is_up(url):
            return
        time.sleep(1)
    raise RuntimeError(f"Frontend did not start at {url}")


def _is_up(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            return response.status < 500
    except (OSError, URLError):
        return False


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
