"""Validate and package the Chrome Web Store extension artifact."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
EXTENSION_DIR = ROOT / "browser-extension"
DIST_DIR = ROOT / "dist"
RUNTIME_FILES = (
    "manifest.json",
    "popup.html",
    "popup.js",
    "content.js",
    "github_injected.js",
    "project_analysis.js",
    "styles.css",
    "assets/icon16.png",
    "assets/icon48.png",
    "assets/icon128.png",
)
ALLOWED_PERMISSIONS = {"activeTab", "scripting", "storage"}
ALLOWED_HOSTS = {"http://127.0.0.1:8765/*", "https://github.com/*"}
SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"gh[oprsu]_[0-9A-Za-z]{30,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def validate_extension(extension_dir: Path = EXTENSION_DIR) -> dict[str, object]:
    """Return the parsed manifest after checking store-release constraints."""
    manifest_path = extension_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != 3:
        raise ValueError("A extensao deve usar Manifest V3.")
    if set(manifest.get("permissions", [])) - ALLOWED_PERMISSIONS:
        raise ValueError("O manifest solicita permissoes alem do conjunto minimo.")
    if set(manifest.get("host_permissions", [])) - ALLOWED_HOSTS:
        raise ValueError("O manifest solicita host permissions inesperadas.")
    if "<all_urls>" in json.dumps(manifest):
        raise ValueError("O manifest nao pode solicitar <all_urls>.")
    for relative in RUNTIME_FILES:
        if not (extension_dir / relative).is_file():
            raise FileNotFoundError(f"Arquivo obrigatorio ausente: {relative}")
    scan_for_secrets(extension_dir)
    return manifest


def scan_for_secrets(extension_dir: Path = EXTENSION_DIR) -> None:
    """Reject real secret values while allowing configuration field names."""
    for relative in RUNTIME_FILES:
        path = extension_dir / relative
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            continue
        content = path.read_text(encoding="utf-8")
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            raise ValueError(f"Possivel segredo encontrado em {relative}.")


def package_extension(
    extension_dir: Path = EXTENSION_DIR,
    output: Path | None = None,
) -> Path:
    """Build a deterministic ZIP containing runtime files only."""
    manifest = validate_extension(extension_dir)
    version = str(manifest["version"])
    target = output or DIST_DIR / f"sotuhire-extension-v{version}.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in RUNTIME_FILES:
            archive.write(extension_dir / relative, relative)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    target = package_extension(output=args.output)
    print(f"Extensao validada e empacotada em {target}")


if __name__ == "__main__":
    main()
