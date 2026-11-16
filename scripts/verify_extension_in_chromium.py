"""Load the distributed Browser Companion ZIP into a real Chromium and use it (C12).

    python scripts/verify_extension_in_chromium.py [--zip path]

Packages the extension with scripts/package_extension.py (unless --zip is given), unzips it into a
temporary folder and loads it with --load-extension in a persistent Chromium context. Then:

1. the MV3 service worker starts and exposes the extension id;
2. the popup page renders without console or page errors;
3. on a GitHub URL (served offline by request interception, fictional content) the extension does
   what the popup's capture does (popup.js extract: inject content.js, send SOTUHIRE_CAPTURE) and
   gets the page's title, URL and text back.

No network, no account, no real data. Prints a JSON report; exit 1 if any step fails.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = """<!doctype html><html><head><title>fictional-org/fictional-repo</title></head>
<body><main><h1>fictional-repo</h1><p>Repositório fictício para teste da extensão.</p>
<article id="readme">Projeto de exemplo com Python e testes.</article></main></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path)
    args = parser.parse_args()
    report: dict[str, object] = {"steps": {}}
    steps: dict[str, object] = report["steps"]  # type: ignore[assignment]
    with tempfile.TemporaryDirectory(prefix="sotuhire-ext-") as work:
        work_dir = Path(work)
        archive = args.zip
        if archive is None:
            archive = work_dir / "extension.zip"
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
        unpacked = work_dir / "unpacked"
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(unpacked)
        manifest_dir = next(p.parent for p in unpacked.rglob("manifest.json"))
        errors: list[str] = []
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(work_dir / "profile"),
                channel="chromium",
                headless=True,
                args=[
                    f"--disable-extensions-except={manifest_dir}",
                    f"--load-extension={manifest_dir}",
                ],
            )
            try:
                worker = (
                    context.service_workers[0]
                    if context.service_workers
                    else context.wait_for_event("serviceworker", timeout=15_000)
                )
                extension_id = worker.url.split("/")[2]
                steps["service_worker"] = {
                    "ok": worker.url.endswith("/background.js"),
                    "url": worker.url,
                }

                popup = context.new_page()
                popup.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                popup.on("pageerror", lambda e: errors.append(str(e)))
                popup.goto(f"chrome-extension://{extension_id}/popup.html")
                popup.wait_for_load_state("domcontentloaded")
                popup.wait_for_timeout(800)
                text = popup.locator("body").inner_text()
                steps["popup"] = {
                    "ok": bool(text.strip()) and not errors,
                    "title": popup.title(),
                    "errors": errors[:5],
                    "chars": len(text),
                }

                context.route(
                    "https://github.com/**",
                    lambda route: route.fulfill(status=200, content_type="text/html", body=FIXTURE),
                )
                page = context.new_page()
                page.goto("https://github.com/fictional-org/fictional-repo")
                page.wait_for_timeout(1_000)
                try:
                    answer = worker.evaluate(
                        """async () => {
                          const [tab] = await chrome.tabs.query({ url: "https://github.com/*" });
                          // the popup's extract() (popup.js): inject content.js, then ask for a capture
                          await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
                          return await chrome.tabs.sendMessage(tab.id, { type: "SOTUHIRE_CAPTURE" });
                        }"""
                    )
                except Exception as exc:  # noqa: BLE001 - reported as the step's failure
                    answer = {"error": str(exc).splitlines()[0]}
                answer = answer if isinstance(answer, dict) else {}
                raw_capture = answer.get("capture")
                capture: dict = raw_capture if isinstance(raw_capture, dict) else {}
                steps["content_script"] = {
                    "ok": "fictional-repo" in json.dumps(capture),
                    "keys": sorted(capture)[:12],
                    "url": capture.get("url"),
                    "error": answer.get("error"),
                }
            finally:
                context.close()
    ok = (
        all(isinstance(step, dict) and step.get("ok") for step in steps.values())
        and len(steps) == 3
    )
    report["ok"] = ok
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
