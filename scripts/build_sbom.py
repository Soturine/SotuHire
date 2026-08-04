"""Build a deterministic CycloneDX inventory for Python and web dependencies."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from importlib import metadata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_LOCK = ROOT / "apps" / "web" / "package-lock.json"


def _name(requirement: str) -> str:
    match = re.match(r"[A-Za-z0-9_.-]+", requirement)
    if match is None:
        raise ValueError(f"Dependência inválida: {requirement}")
    return match.group(0)


def _python_components(project: dict[str, Any]) -> list[dict[str, str]]:
    requirements = [
        *project["project"].get("dependencies", []),
        *project["project"].get("optional-dependencies", {}).get("dev", []),
        *project["project"].get("optional-dependencies", {}).get("ai", []),
    ]
    components: list[dict[str, str]] = []
    for requirement in requirements:
        name = _name(requirement)
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = "not-installed"
        components.append(
            {
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:pypi/{name.lower()}@{version}",
                "scope": "required"
                if requirement in project["project"]["dependencies"]
                else "optional",
            }
        )
    return components


def _web_components(lock: dict[str, Any]) -> list[dict[str, str]]:
    root_package = lock.get("packages", {}).get("", {})
    declared = {
        **root_package.get("dependencies", {}),
        **root_package.get("devDependencies", {}),
    }
    components: list[dict[str, str]] = []
    for name in sorted(declared, key=str.casefold):
        installed = lock.get("packages", {}).get(f"node_modules/{name}", {})
        version = str(installed.get("version", declared[name]))
        components.append(
            {
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:npm/{name.replace('@', '%40')}@{version}",
                "scope": "optional"
                if name in root_package.get("devDependencies", {})
                else "required",
            }
        )
    return components


def build_sbom() -> dict[str, Any]:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    app_version = str(project["project"]["version"])
    components = [*_python_components(project), *_web_components(lock)]
    components.sort(key=lambda item: (item["purl"].casefold(), item["version"]))
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "sotuhire",
                "version": app_version,
                "purl": f"pkg:pypi/sotuhire@{app_version}",
            }
        },
        "components": components,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sbom = build_sbom()
    output = args.output or ROOT / "dist" / (
        f"sotuhire-sbom-v{sbom['metadata']['component']['version']}.cdx.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sbom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"SBOM CycloneDX gerado: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
