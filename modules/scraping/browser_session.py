"""Manage a persistent user-authenticated Chromium session exposed through CDP."""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

DEFAULT_CDP_URL = "http://127.0.0.1:9222"


@dataclass(frozen=True)
class BrowserSessionStatus:
    """Current availability of the local authenticated browser session."""

    available: bool
    endpoint: str
    browser: str = ""
    message: str = ""


def normalize_cdp_endpoint(endpoint: str) -> str:
    """Validate and normalize a loopback-only CDP endpoint."""
    clean = endpoint.strip().rstrip("/") or DEFAULT_CDP_URL
    parsed = urlparse(clean)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("O endpoint CDP deve usar HTTP local, como http://127.0.0.1:9222.")
    if parsed.port is None:
        raise ValueError("O endpoint CDP precisa informar uma porta.")
    return clean


def inspect_browser_session(
    endpoint: str = DEFAULT_CDP_URL,
    *,
    opener: Callable[..., Any] = urlopen,
    timeout_seconds: float = 0.4,
) -> BrowserSessionStatus:
    """Return a friendly status for the local CDP endpoint."""
    try:
        normalized = normalize_cdp_endpoint(endpoint)
        with opener(f"{normalized}/json/version", timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return BrowserSessionStatus(
            available=bool(payload.get("webSocketDebuggerUrl")),
            endpoint=normalized,
            browser=str(payload.get("Browser", "Chromium")),
            message="Navegador autenticado conectado e pronto.",
        )
    except Exception as exc:
        return BrowserSessionStatus(
            available=False,
            endpoint=endpoint,
            message=(
                str(exc)
                if isinstance(exc, ValueError)
                else "Nenhum navegador do SotuHire está ouvindo neste endpoint."
            ),
        )


def find_chromium_executable() -> Path:
    """Locate Chrome, Edge, or the Playwright Chromium executable."""
    candidates = [
        os.getenv("SOTUHIRE_BROWSER_PATH", ""),
        str(Path(os.getenv("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"),
        str(Path(os.getenv("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe"),
        str(Path(os.getenv("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe"),
        str(Path(os.getenv("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe"),
        str(Path(os.getenv("PROGRAMFILES(X86)", "")) / "Microsoft/Edge/Application/msedge.exe"),
    ]
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            candidates.append(playwright.chromium.executable_path)
    except Exception:
        pass
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise FileNotFoundError(
        "Chrome, Edge ou Chromium não foi encontrado. "
        "Defina SOTUHIRE_BROWSER_PATH com o caminho do executável."
    )


def default_profile_dir() -> Path:
    """Return the persistent profile used only by the SotuHire browser."""
    local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home()))
    return local_app_data / "SotuHire" / "authenticated-browser-profile"


def launch_authenticated_browser(
    start_url: str,
    endpoint: str = DEFAULT_CDP_URL,
    *,
    executable: str | Path | None = None,
    profile_dir: str | Path | None = None,
    popen: Callable[..., Any] = subprocess.Popen,
    sleeper: Callable[[float], None] = time.sleep,
    status_checker: Callable[[str], BrowserSessionStatus] = inspect_browser_session,
    timeout_seconds: float = 12,
) -> BrowserSessionStatus:
    """Open or reuse a visible persistent browser prepared for manual login."""
    normalized = normalize_cdp_endpoint(endpoint)
    current = status_checker(normalized)
    if current.available:
        return current
    parsed = urlparse(normalized)
    browser_path = Path(executable) if executable else find_chromium_executable()
    target_profile = Path(profile_dir) if profile_dir else default_profile_dir()
    target_profile.mkdir(parents=True, exist_ok=True)
    command = [
        str(browser_path),
        f"--remote-debugging-port={parsed.port}",
        f"--user-data-dir={target_profile}",
        "--no-first-run",
        "--no-default-browser-check",
        start_url.strip() or "https://www.linkedin.com/jobs/",
    ]
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        sleeper(0.4)
        current = status_checker(normalized)
        if current.available:
            return BrowserSessionStatus(
                available=True,
                endpoint=normalized,
                browser=current.browser,
                message=(
                    "Navegador do SotuHire aberto. Faça login manualmente nele e depois inicie "
                    "a coleta."
                ),
            )
    return BrowserSessionStatus(
        available=False,
        endpoint=normalized,
        message="O navegador foi iniciado, mas o endpoint CDP não respondeu a tempo.",
    )
