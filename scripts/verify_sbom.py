"""Fail when a CycloneDX SBOM is missing, mismatched or claims less than the lockfile holds.

Used by CI right after ``build_sbom.py`` so a green job always means the artifact exists,
names the current project version, covers every package resolved in
``apps/web/package-lock.json`` and has no dangling dependency references.
"""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_LOCK = ROOT / "apps" / "web" / "package-lock.json"


def verify_sbom(
    sbom: dict[str, Any], *, project: dict[str, Any], lock: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if sbom.get("bomFormat") != "CycloneDX":
        errors.append("bomFormat is not CycloneDX")
    expected_version = str(project["project"]["version"])
    component = sbom.get("metadata", {}).get("component", {})
    if component.get("version") != expected_version:
        errors.append(
            f"SBOM describes sotuhire {component.get('version')!r}, project is {expected_version!r}"
        )
    properties = {
        item.get("name"): item.get("value")
        for item in sbom.get("metadata", {}).get("properties", [])
    }
    if properties.get("sotuhire:sbom:python-complete") != "true":
        errors.append("Python closure incomplete: some requirements were not installed")
    components = sbom.get("components", [])
    purls = {item.get("purl") for item in components}
    for path, entry in lock.get("packages", {}).items():
        if not path or entry.get("link") or "version" not in entry:
            continue
        name = entry.get("name") or path.rsplit("node_modules/", 1)[-1]
        purl = f"pkg:npm/{name.replace('@', '%40')}@{entry['version']}"
        if purl not in purls:
            errors.append(f"lockfile package missing from SBOM: {purl}")
    refs = {item.get("bom-ref") for item in components} | {component.get("bom-ref")}
    for dependency in sbom.get("dependencies", []):
        for ref in [dependency.get("ref"), *dependency.get("dependsOn", [])]:
            if ref not in refs:
                errors.append(f"dangling dependency reference: {ref}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sbom", type=Path)
    args = parser.parse_args()
    if not args.sbom.is_file():
        print(f"SBOM ausente: {args.sbom}")
        return 1
    errors = verify_sbom(
        json.loads(args.sbom.read_text(encoding="utf-8")),
        project=tomllib.loads(PYPROJECT.read_text(encoding="utf-8")),
        lock=json.loads(PACKAGE_LOCK.read_text(encoding="utf-8")),
    )
    for error in errors:
        print(error)
    if errors:
        return 1
    print(f"SBOM verificado: {args.sbom}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
