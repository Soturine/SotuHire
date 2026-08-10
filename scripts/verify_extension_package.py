"""Verify the packaged extension has the exact safe runtime payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

try:
    from scripts.package_extension import DIST_DIR, RUNTIME_FILES, validate_extension
except ModuleNotFoundError:  # execução direta: python scripts/verify_extension_package.py
    from package_extension import DIST_DIR, RUNTIME_FILES, validate_extension


def verify_package(path: Path) -> dict[str, object]:
    expected_manifest = validate_extension()
    expected_names = set(RUNTIME_FILES)
    try:
        with ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("ZIP contém entradas duplicadas.")
            if set(names) != expected_names:
                missing = sorted(expected_names - set(names))
                unexpected = sorted(set(names) - expected_names)
                raise ValueError(f"Payload divergente; ausentes={missing}; extras={unexpected}")
            for name in names:
                pure = PurePosixPath(name)
                if pure.is_absolute() or ".." in pure.parts or "\\" in name:
                    raise ValueError(f"Entrada insegura no ZIP: {name}")
            packaged_manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    except BadZipFile as exc:
        raise ValueError("Artefato não é um ZIP válido.") from exc
    if packaged_manifest != expected_manifest:
        raise ValueError("Manifest empacotado diverge do manifest validado.")
    if packaged_manifest.get("version") != "0.10.0":
        raise ValueError("A release v1.11.0 exige extensão 0.10.0.")
    return packaged_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=DIST_DIR / "sotuhire-extension-v0.10.0.zip",
    )
    args = parser.parse_args()
    manifest = verify_package(args.path)
    print(f"Pacote da extensão v{manifest['version']} verificado: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
