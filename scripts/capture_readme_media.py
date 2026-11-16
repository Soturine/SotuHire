"""Capture the README screenshots and demo GIF/WebM from the real production build.

    cd apps/web && npx vite build && cd ../..
    python scripts/capture_readme_media.py

Serves apps/web/dist with `vite preview` on 127.0.0.1:4173, opens it in Chromium in sample mode
(the fictional persona the app ships with; no API, no personal data) and writes:

* docs/assets/screenshots/app/*.png   one screen each, 1440x900 (mobile: 390x844)
* docs/assets/demo/sotuhire-demo.gif  a short tour built from frames of the running app
* docs/assets/demo/sotuhire-demo.webm the same tour recorded by the browser

Nothing is drawn or mocked up: every frame is a capture of the built app.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
SHOTS = ROOT / "docs" / "assets" / "screenshots" / "app"
DEMO = ROOT / "docs" / "assets" / "demo"
BASE = "http://127.0.0.1:4173"

SCREENS = [
    ("cockpit", "/dashboard"),
    ("profile", "/profile"),
    ("resume-studio", "/resume-studio"),
    ("radar", "/radar"),
    ("tracker", "/tracker"),
    ("application-lab", "/application-lab"),
    ("approvals", "/approvals"),
]
TOUR = [
    ("home", "/"),
    ("cockpit", "/dashboard"),
    ("profile", "/profile"),
    ("resume-studio", "/resume-studio"),
    ("radar", "/radar"),
    ("tracker", "/tracker"),
    ("copilot", "/dashboard"),
    ("approvals", "/approvals"),
]
INIT = """
localStorage.setItem('sotuhire.onboarding.v1.complete', 'true');
localStorage.setItem('sotuhire.api-mode', 'demo');
"""


def wait_http(url: str, timeout: float = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3):  # noqa: S310 - loopback
                return
        except Exception:  # noqa: BLE001 - still starting
            time.sleep(0.5)
    raise RuntimeError(f"{url} did not answer")


def settle(page: Page) -> None:
    page.wait_for_load_state("networkidle")
    page.wait_for_function(
        "() => !document.querySelector('[aria-busy=\"true\"], .animate-spin')", timeout=15_000
    )
    page.wait_for_timeout(900)  # sample-mode latency (400-800 ms) and entrance motion


def show(page: Page, name: str, path: str) -> None:
    page.goto(BASE + path)
    settle(page)
    if name == "copilot":
        page.get_by_role("button", name="Copilot").first.click()
        page.wait_for_timeout(1200)


def frames_to_gif(frames: list[Path], target: Path, width: int = 960) -> None:
    hold_ms, fade_steps, fade_ms = 1700, 4, 70
    images = []
    durations = []
    resized = []
    for path in frames:
        image = Image.open(path).convert("RGB")
        height = round(image.height * width / image.width)
        resized.append(image.resize((width, height), Image.Resampling.LANCZOS))
    for index, image in enumerate(resized):
        images.append(image)
        durations.append(hold_ms)
        following = resized[(index + 1) % len(resized)]
        for step in range(1, fade_steps + 1):
            images.append(Image.blend(image, following, step / (fade_steps + 1)))
            durations.append(fade_ms)
    palette = images[0].quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    quantized = [img.quantize(palette=palette, dither=Image.Dither.NONE) for img in images]
    quantized[0].save(
        target,
        save_all=True,
        append_images=quantized[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=1,
    )


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    DEMO.mkdir(parents=True, exist_ok=True)
    npx = shutil.which("npx") or "npx"
    log = (ROOT / ".pytest_cache" / "capture-preview.log").open("w", encoding="utf-8")
    preview = subprocess.Popen(
        [npx, "vite", "preview", "--port", "4173", "--strictPort", "--host", "127.0.0.1"],
        cwd=WEB,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_http(BASE + "/")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                locale="pt-BR",
                color_scheme="light",
                reduced_motion="reduce",
            )
            context.add_init_script(INIT)
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            for name, path in SCREENS:
                show(page, name, path)
                page.screenshot(path=str(SHOTS / f"{name}.png"))
            show(page, "copilot", "/dashboard")
            page.screenshot(path=str(SHOTS / "copilot.png"))
            context.close()

            dark = browser.new_context(
                viewport={"width": 1440, "height": 900}, locale="pt-BR", color_scheme="dark"
            )
            dark.add_init_script(INIT)
            page = dark.new_page()
            show(page, "cockpit", "/dashboard")
            page.screenshot(path=str(SHOTS / "cockpit-dark.png"))
            dark.close()

            mobile = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True,
                locale="pt-BR",
            )
            mobile.add_init_script(INIT)
            page = mobile.new_page()
            show(page, "cockpit", "/dashboard")
            page.screenshot(path=str(SHOTS / "mobile-cockpit.png"))
            show(page, "tracker", "/tracker")
            page.screenshot(path=str(SHOTS / "mobile-tracker.png"))
            mobile.close()

            frames_dir = ROOT / ".pytest_cache" / "readme-frames"
            shutil.rmtree(frames_dir, ignore_errors=True)
            frames_dir.mkdir(parents=True)
            video_dir = ROOT / ".pytest_cache" / "readme-video"
            shutil.rmtree(video_dir, ignore_errors=True)
            tour = browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="pt-BR",
                record_video_dir=str(video_dir),
                record_video_size={"width": 1280, "height": 800},
            )
            tour.add_init_script(INIT)
            page = tour.new_page()
            frames = []
            for index, (name, path) in enumerate(TOUR):
                show(page, name, path)
                frame = frames_dir / f"{index:02d}-{name}.png"
                page.screenshot(path=str(frame))
                frames.append(frame)
                page.wait_for_timeout(1200)  # let the recording dwell on each screen
            if page.video is None:
                raise RuntimeError("the tour was not recorded")
            video_path = Path(page.video.path())
            tour.close()
            shutil.copyfile(video_path, DEMO / "sotuhire-demo.webm")
            frames_to_gif(frames, DEMO / "sotuhire-demo.gif")
            browser.close()
            if errors:
                print("page errors:", errors[:5])
    finally:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(preview.pid)], capture_output=True)
        else:
            preview.terminate()
        preview.wait(timeout=15)
        log.close()
    for path in sorted([*SHOTS.glob("*.png"), *DEMO.iterdir()]):
        print(f"{path.relative_to(ROOT).as_posix()}  {path.stat().st_size // 1024} KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
