"""Build a deterministic CycloneDX inventory for Python and web dependencies.

Scope, stated in the document itself (``metadata.properties``):

- web: every package resolved in ``apps/web/package-lock.json`` (direct and transitive),
  with its lockfile version, scope (dev or runtime) and dependency edges;
- Python: the transitive closure of the project requirements (runtime + ``dev`` + ``ai``
  extras) as installed in the environment that runs this script. SotuHire has no Python
  lockfile, so these versions describe *that* environment, not a pinned resolution.
  Requirements that are not installed are listed with version ``not-installed`` and the
  document is marked incomplete instead of silently dropping them.
"""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from importlib import metadata
from pathlib import Path
from typing import Any

from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_LOCK = ROOT / "apps" / "web" / "package-lock.json"
PYTHON_EXTRAS = ("dev", "ai")


def _name(requirement: str) -> str:
    match = re.match(r"[A-Za-z0-9_.-]+", requirement)
    if match is None:
        raise ValueError(f"Dependência inválida: {requirement}")
    return match.group(0)


def _marker_applies(requirement: Requirement, extras: set[str]) -> bool:
    if requirement.marker is None:
        return True
    environment: dict[str, str] = {key: str(value) for key, value in default_environment().items()}
    return any(
        requirement.marker.evaluate({**environment, "extra": extra}) for extra in (extras or {""})
    )


def _python_components(
    project: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool, list[str]]:
    declared = project["project"].get("dependencies", [])
    optional = project["project"].get("optional-dependencies", {})
    roots: list[tuple[Requirement, str]] = [(Requirement(item), "required") for item in declared]
    for extra in PYTHON_EXTRAS:
        roots.extend((Requirement(item), "optional") for item in optional.get(extra, []))

    components: dict[str, dict[str, Any]] = {}
    edges: dict[str, set[str]] = {}
    complete = True
    missing: dict[str, str] = {}
    queue: list[tuple[Requirement, str]] = list(roots)
    requested_extras: dict[str, set[str]] = {}
    while queue:
        requirement, scope = queue.pop(0)
        key = canonicalize_name(requirement.name)
        known_extras = requested_extras.setdefault(key, set())
        new_extras = set(requirement.extras) - known_extras
        if key in components:
            if scope == "required":
                components[key]["scope"] = "required"
            if not new_extras:
                continue
        known_extras.update(new_extras)
        try:
            distribution = metadata.distribution(requirement.name)
            version = distribution.version
        except metadata.PackageNotFoundError:
            # A missing runtime requirement makes the inventory incomplete; a missing
            # optional extra (e.g. ``ai`` in a dev-only install) is reported, not invented.
            if scope == "required":
                complete = False
            missing[key] = scope
            continue
        components.setdefault(key, _python_component(key, version, scope))
        ref = components[key]["bom-ref"]
        for raw in distribution.requires or []:
            try:
                child = Requirement(raw)
            except InvalidRequirement:
                continue
            if not _marker_applies(child, known_extras):
                continue
            queue.append((child, scope))
            edges.setdefault(ref, set()).add(canonicalize_name(child.name))

    by_name = {name: item["bom-ref"] for name, item in components.items()}
    dependencies = [
        {"ref": ref, "dependsOn": sorted(by_name[name] for name in children if name in by_name)}
        for ref, children in sorted(edges.items())
    ]
    return list(components.values()), dependencies, complete, sorted(missing)


def _python_component(name: str, version: str, scope: str) -> dict[str, Any]:
    purl = f"pkg:pypi/{name}@{version}"
    return {
        "type": "library",
        "bom-ref": purl,
        "name": name,
        "version": version,
        "purl": purl,
        "scope": scope,
    }


def _npm_name(path: str, entry: dict[str, Any]) -> str:
    if entry.get("name"):
        return str(entry["name"])
    return path.rsplit("node_modules/", 1)[-1]


def _web_components(
    lock: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    packages: dict[str, dict[str, Any]] = lock.get("packages", {})
    components: dict[str, dict[str, Any]] = {}
    path_ref: dict[str, str] = {}
    for path, entry in sorted(packages.items()):
        if not path or entry.get("link") or "version" not in entry:
            continue
        name = _npm_name(path, entry)
        version = str(entry["version"])
        purl = f"pkg:npm/{name.replace('@', '%40')}@{version}"
        path_ref[path] = purl
        component = components.setdefault(
            purl,
            {
                "type": "library",
                "bom-ref": purl,
                "name": name,
                "version": version,
                "purl": purl,
                "scope": "optional" if entry.get("dev") else "required",
            },
        )
        if not entry.get("dev"):
            component["scope"] = "required"

    def resolve(from_path: str, dependency: str) -> str | None:
        # Node resolution: nearest node_modules walking up from the requiring package.
        base = from_path
        while True:
            candidate = (
                f"{base}/node_modules/{dependency}" if base else f"node_modules/{dependency}"
            )
            if candidate in path_ref:
                return path_ref[candidate]
            if not base:
                return None
            base = base.rsplit("/node_modules/", 1)[0] if "/node_modules/" in base else ""

    edges: dict[str, set[str]] = {}
    for path, entry in packages.items():
        if path not in path_ref:
            continue
        for dependency in {
            **entry.get("dependencies", {}),
            **entry.get("optionalDependencies", {}),
        }:
            target = resolve(path, dependency)
            if target is not None:
                edges.setdefault(path_ref[path], set()).add(target)
    dependencies = [
        {"ref": ref, "dependsOn": sorted(children)} for ref, children in sorted(edges.items())
    ]
    return list(components.values()), dependencies, path_ref


def build_sbom() -> dict[str, Any]:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    app_version = str(project["project"]["version"])
    python_components, python_dependencies, python_complete, python_missing = _python_components(
        project
    )
    web_components, web_dependencies, web_paths = _web_components(lock)
    components = [*python_components, *web_components]
    components.sort(key=lambda item: (item["purl"].casefold(), item["version"]))
    app_ref = f"pkg:pypi/sotuhire@{app_version}"
    optional = project["project"].get("optional-dependencies", {})
    direct_python = {
        canonicalize_name(_name(requirement))
        for requirement in [
            *project["project"].get("dependencies", []),
            *(item for extra in PYTHON_EXTRAS for item in optional.get(extra, [])),
        ]
    }
    root_package = lock.get("packages", {}).get("", {})
    direct_web = {
        f"node_modules/{name}"
        for name in {
            **root_package.get("dependencies", {}),
            **root_package.get("devDependencies", {}),
        }
    }
    direct = sorted(
        {item["bom-ref"] for item in python_components if item["name"] in direct_python}
        | {web_paths[path] for path in direct_web if path in web_paths}
    )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "bom-ref": app_ref,
                "name": "sotuhire",
                "version": app_version,
                "purl": app_ref,
            },
            "properties": [
                {"name": "sotuhire:sbom:web-source", "value": "apps/web/package-lock.json"},
                {
                    "name": "sotuhire:sbom:python-source",
                    "value": "installed-environment (no Python lockfile)",
                },
                {
                    "name": "sotuhire:sbom:python-complete",
                    "value": "true" if python_complete else "false",
                },
                {
                    "name": "sotuhire:sbom:python-not-installed",
                    "value": ",".join(python_missing),
                },
            ],
        },
        "components": components,
        "dependencies": [
            {"ref": app_ref, "dependsOn": direct},
            *sorted(python_dependencies + web_dependencies, key=lambda item: item["ref"]),
        ],
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
