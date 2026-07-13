"""Validate the capability manifest against the running API and repository tree."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "capabilities.json"
ENDPOINT_PATTERN = re.compile(r"^(GET|POST|PUT|PATCH|DELETE) (/api/\S+)$")
FRONTEND_ROUTE_PATTERN = re.compile(r"createFileRoute\(\s*[\"']([^\"']+)[\"']\s*\)")
REQUIRED_FIELDS = {
    "capability_id",
    "label",
    "frontend_route",
    "api_endpoints",
    "backend_services",
    "core_modules",
    "stores",
    "profile_integration",
    "context_purpose",
    "ai_support",
    "extension_support",
    "dedupe_strategy",
    "snapshot_support",
    "tests",
    "docs",
    "status",
    "gaps",
    "last_verified_commit",
}
ALLOWED_STATUSES = {"complete", "partial", "legacy"}


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load a JSON manifest and require an object at the root."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("O manifesto deve conter um objeto JSON na raiz.")
    return payload


def openapi_operations() -> set[str]:
    """Return method/path pairs declared by the real FastAPI OpenAPI document."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from apps.api.main import create_app

    operations: set[str] = set()
    for path, path_spec in create_app().openapi().get("paths", {}).items():
        for method in path_spec:
            normalized = method.upper()
            if normalized in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                operations.add(f"{normalized} {path}")
    return operations


def frontend_routes(root: Path = ROOT) -> set[str]:
    """Read TanStack file-route declarations instead of trusting generated docs."""
    routes: set[str] = set()
    route_dir = root / "apps" / "web" / "src" / "routes"
    for source in sorted(route_dir.glob("*.tsx")):
        routes.update(FRONTEND_ROUTE_PATTERN.findall(source.read_text(encoding="utf-8")))
    return routes


def context_purposes() -> set[str]:
    """Return context purposes supported by the actual engine model."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from modules.context.models import CareerContextPurpose

    return {purpose.value for purpose in CareerContextPurpose}


def prompt_ids() -> set[str]:
    """Return prompt ids registered by the application."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from modules.ai.prompt_loader import default_prompt_registry

    return set(default_prompt_registry().list_prompt_ids())


def validate_manifest(
    manifest: dict[str, Any],
    *,
    root: Path = ROOT,
    api_operations: set[str] | None = None,
    web_routes: set[str] | None = None,
    valid_context_purposes: set[str] | None = None,
    registered_prompt_ids: set[str] | None = None,
) -> list[str]:
    """Return deterministic validation errors; an empty list means valid."""
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version deve ser 1")
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        return [*errors, "capabilities deve ser uma lista não vazia"]

    operations = api_operations if api_operations is not None else openapi_operations()
    routes = web_routes if web_routes is not None else frontend_routes(root)
    purposes = valid_context_purposes if valid_context_purposes is not None else context_purposes()
    prompts = registered_prompt_ids if registered_prompt_ids is not None else prompt_ids()
    seen_ids: set[str] = set()

    for index, raw_capability in enumerate(capabilities):
        if not isinstance(raw_capability, dict):
            errors.append(f"capabilities[{index}] deve ser um objeto")
            continue
        capability = raw_capability
        capability_id = str(capability.get("capability_id", f"índice-{index}"))
        missing = sorted(REQUIRED_FIELDS - capability.keys())
        if missing:
            errors.append(f"{capability_id}: campos ausentes: {', '.join(missing)}")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", capability_id):
            errors.append(f"{capability_id}: capability_id inválido")
        if capability_id in seen_ids:
            errors.append(f"{capability_id}: capability_id duplicado")
        seen_ids.add(capability_id)

        route = capability.get("frontend_route")
        if route is not None and (not isinstance(route, str) or route not in routes):
            errors.append(f"{capability_id}: rota frontend não encontrada: {route}")

        declared_endpoints = capability.get("api_endpoints", [])
        if not isinstance(declared_endpoints, list):
            errors.append(f"{capability_id}: api_endpoints deve ser uma lista")
        else:
            for endpoint in declared_endpoints:
                if not isinstance(endpoint, str) or not ENDPOINT_PATTERN.fullmatch(endpoint):
                    errors.append(f"{capability_id}: endpoint inválido: {endpoint}")
                elif endpoint not in operations:
                    errors.append(f"{capability_id}: endpoint ausente no OpenAPI: {endpoint}")

        for field in ("backend_services", "core_modules", "stores", "tests", "docs"):
            _validate_paths(errors, capability_id, field, capability.get(field), root)

        purpose = capability.get("context_purpose")
        if purpose is not None and purpose not in purposes:
            errors.append(f"{capability_id}: context_purpose desconhecido: {purpose}")

        ai_support = capability.get("ai_support")
        if not isinstance(ai_support, dict):
            errors.append(f"{capability_id}: ai_support deve ser um objeto")
        else:
            for field in ("enabled", "prompt_ids", "providers", "fallback"):
                if field not in ai_support:
                    errors.append(f"{capability_id}: ai_support.{field} ausente")
            if not isinstance(ai_support.get("enabled"), bool):
                errors.append(f"{capability_id}: ai_support.enabled deve ser booleano")
            declared_prompts = ai_support.get("prompt_ids", [])
            if not isinstance(declared_prompts, list):
                errors.append(f"{capability_id}: ai_support.prompt_ids deve ser uma lista")
                declared_prompts = []
            providers = ai_support.get("providers")
            if not isinstance(providers, list) or not providers:
                errors.append(f"{capability_id}: ai_support.providers deve ser lista não vazia")
            if not isinstance(ai_support.get("fallback"), str):
                errors.append(f"{capability_id}: ai_support.fallback deve ser texto")
            for prompt_id in declared_prompts:
                if prompt_id not in prompts:
                    errors.append(f"{capability_id}: prompt não registrado: {prompt_id}")

        status = capability.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{capability_id}: status inválido: {status}")
        if not str(capability.get("last_verified_commit", "")).strip():
            errors.append(f"{capability_id}: last_verified_commit vazio")
        if not isinstance(capability.get("gaps"), list):
            errors.append(f"{capability_id}: gaps deve ser uma lista")

    return sorted(set(errors))


def _validate_paths(
    errors: list[str],
    capability_id: str,
    field: str,
    value: object,
    root: Path,
) -> None:
    if not isinstance(value, list):
        errors.append(f"{capability_id}: {field} deve ser uma lista")
        return
    if field in {"backend_services", "core_modules", "tests", "docs"} and not value:
        errors.append(f"{capability_id}: {field} não pode ficar vazio")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{capability_id}: caminho inválido em {field}: {item}")
            continue
        candidate = (root / item).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{capability_id}: caminho fora do repositório em {field}: {item}")
            continue
        if not candidate.is_file():
            errors.append(f"{capability_id}: arquivo ausente em {field}: {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        errors = validate_manifest(manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Capabilities manifest inválido: {exc}")
        return 1
    if errors:
        print("Capabilities manifest inválido:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "Capabilities manifest válido: "
        f"{len(manifest['capabilities'])} capacidades, OpenAPI/rotas/arquivos/prompts conferidos."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
