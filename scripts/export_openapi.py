"""Write the Local API's OpenAPI document where the web client's contract test reads it.

    python scripts/export_openapi.py            # refresh apps/web/tests/contract/openapi.json
    python scripts/export_openapi.py --check    # exit 1 if the committed copy is stale

The web test `src/lib/api/contract.test.ts` sends the client's real request bodies through this
document: every request model forbids unknown fields, so a field the client adds (SH-NEW-032) is a
422 in API mode that sample mode never shows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "apps" / "web" / "tests" / "contract" / "openapi.json"


# Keys that state the contract. Titles, descriptions, defaults, examples and the 422 responses
# FastAPI adds on its own change between FastAPI/Pydantic versions without changing the API (CI
# installs the latest compatible versions), so they are left out of the committed view.
_CONTRACT_KEYS = {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "anyOf",
    "allOf",
    "oneOf",
    "$ref",
    "enum",
    "const",
    "format",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minItems",
    "maxItems",
    "pattern",
}


def _ref_name(ref: str) -> str:
    # Pydantic may split a model into Name-Input / Name-Output depending on its version.
    name = ref.rsplit("/", 1)[-1]
    for suffix in ("-Input", "-Output"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def _normalize(schema):
    if isinstance(schema, list):
        return [_normalize(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    out = {}
    for key, value in schema.items():
        if key not in _CONTRACT_KEYS:
            continue
        if key == "$ref":
            out[key] = "#/components/schemas/" + _ref_name(value)
        elif key == "properties":
            out[key] = {name: _normalize(prop) for name, prop in sorted(value.items())}
        elif key == "required":
            out[key] = sorted(value)
        elif key in ("anyOf", "oneOf", "allOf"):
            items = [_normalize(item) for item in value]
            out[key] = sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
        else:
            out[key] = _normalize(value)
    return out


def contract_view(spec: dict) -> dict:
    """Request bodies, 2xx response bodies and the schemas they reach, normalized."""
    paths: dict = {}
    roots: list = []
    for path, operations in sorted(spec["paths"].items()):
        for method, operation in sorted(operations.items()):
            if not isinstance(operation, dict):
                continue
            entry: dict = {}
            body = operation.get("requestBody", {}).get("content", {}).get("application/json")
            if body:
                schema = _normalize(body["schema"])
                entry["requestBody"] = {"content": {"application/json": {"schema": schema}}}
                roots.append(schema)
            responses = {}
            for code, response in sorted(operation.get("responses", {}).items()):
                content = response.get("content", {}).get("application/json")
                if code.startswith("2") and content and content.get("schema"):
                    schema = _normalize(content["schema"])
                    responses[code] = {"content": {"application/json": {"schema": schema}}}
                    roots.append(schema)
            if responses:
                entry["responses"] = responses
            if entry:
                paths.setdefault(path, {})[method] = entry
    raw = spec.get("components", {}).get("schemas", {})
    by_name: dict = {}
    for name, schema in raw.items():
        by_name.setdefault(_ref_name(name), schema)  # Input and Output carry the same fields here
    reached: dict = {}
    pending = list(roots)
    while pending:
        node = pending.pop()
        if isinstance(node, list):
            pending.extend(node)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key == "$ref":
                    name = _ref_name(value)
                    if name not in reached and name in by_name:
                        reached[name] = _normalize(by_name[name])
                        pending.append(reached[name])
                else:
                    pending.append(value)
    # additionalProperties decides a 422 on what the client sends; on what it only reads it does not,
    # and newer Pydantic emits it for serialization schemas where older versions did not. Keep it
    # on schemas a request body reaches, drop it on response-only ones.
    request_side: set[str] = set()
    pending = [
        entry["requestBody"]
        for ops in paths.values()
        for entry in ops.values()
        if "requestBody" in entry
    ]
    while pending:
        node = pending.pop()
        if isinstance(node, list):
            pending.extend(node)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key == "$ref":
                    name = _ref_name(value)
                    if name not in request_side and name in reached:
                        request_side.add(name)
                        pending.append(reached[name])
                else:
                    pending.append(value)

    def _without_extra(node):
        if isinstance(node, list):
            return [_without_extra(item) for item in node]
        if isinstance(node, dict):
            return {k: _without_extra(v) for k, v in node.items() if k != "additionalProperties"}
        return node

    schemas = {
        name: schema if name in request_side else _without_extra(schema)
        for name, schema in sorted(reached.items())
    }
    return {"paths": paths, "components": {"schemas": schemas}}


def render() -> str:
    sys.path.insert(0, str(ROOT))
    from apps.api.main import app

    view = contract_view(app.openapi())
    return json.dumps(view, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != text:
            print(f"{TARGET.relative_to(ROOT)} is stale; run scripts/export_openapi.py")
            return 1
        return 0
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
