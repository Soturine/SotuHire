"""Capture MkDocs screenshots for the public SotuHire site."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "assets" / "screenshots"

DESKTOP_PAGES = {
    "sotuhire-v1.1-home.png": "",
    "sotuhire-v1.1-demo.png": "08-frontend/static-demo/",
    "sotuhire-v1.1-frontend-handoff.png": "08-frontend/lovable-handoff/",
    "sotuhire-v1.1-application-intelligence.png": "08-frontend/application-intelligence/",
}

GIF_FRAMES = {
    "frame-01-home.png": "",
    "frame-02-demo.png": "08-frontend/static-demo/",
    "frame-03-match.png": "07-development/v0.12.0-match-engine-2/",
    "frame-04-application-intelligence.png": "08-frontend/application-intelligence/",
    "frame-05-frontend-handoff.png": "08-frontend/lovable-handoff/",
}


def page_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path}"


def goto_checked(page, url: str) -> None:
    response = page.goto(url, wait_until="load", timeout=60_000)
    if response is not None and response.status >= 400:
        raise RuntimeError(f"Failed to load {url}: HTTP {response.status}")
    page.wait_for_timeout(800)


def capture(base_url: str, include_gif: bool) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)

        for filename, path in DESKTOP_PAGES.items():
            goto_checked(page, page_url(base_url, path))
            page.screenshot(path=SCREENSHOT_DIR / filename, full_page=True)

        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 900},
            device_scale_factor=1,
            is_mobile=True,
        )
        goto_checked(mobile_page, page_url(base_url, ""))
        mobile_page.screenshot(
            path=SCREENSHOT_DIR / "sotuhire-v1.1-home-mobile.png", full_page=True
        )

        if include_gif:
            frame_dir = SCREENSHOT_DIR / "_walkthrough_frames"
            frame_dir.mkdir(parents=True, exist_ok=True)
            frame_page = browser.new_page(
                viewport={"width": 1440, "height": 900}, device_scale_factor=1
            )

            for filename, path in GIF_FRAMES.items():
                goto_checked(frame_page, page_url(base_url, path))
                frame_page.screenshot(path=frame_dir / filename, full_page=False)

            browser.close()
            build_gif(frame_dir)
            shutil.rmtree(frame_dir, ignore_errors=True)
            return

        browser.close()


def build_gif(frame_dir: Path) -> None:
    magick = shutil.which("magick")
    if not magick:
        print("ImageMagick not found; GIF was not generated.")
        return

    output = SCREENSHOT_DIR / "sotuhire-v1.1-site-walkthrough.gif"
    frames = [str(frame_dir / name) for name in GIF_FRAMES]
    command = [magick, "-delay", "120", "-loop", "0", *frames, str(output)]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/SotuHire/")
    parser.add_argument("--gif", action="store_true")
    args = parser.parse_args()

    capture(args.base_url, include_gif=args.gif)


if __name__ == "__main__":
    main()
