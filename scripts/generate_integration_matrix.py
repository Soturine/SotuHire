"""Generate the integration capability matrix from config/capabilities.json."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from scripts.validate_capabilities import (
        DEFAULT_MANIFEST,
        ROOT,
        load_manifest,
        validate_manifest,
    )
except ModuleNotFoundError:  # execução direta: python scripts/generate_integration_matrix.py
    from validate_capabilities import DEFAULT_MANIFEST, ROOT, load_manifest, validate_manifest

DEFAULT_OUTPUT = ROOT / "docs" / "02-architecture" / "integration-capability-matrix.md"


def render_matrix(manifest: dict[str, Any]) -> str:
    """Render an atemporal, deterministic Markdown matrix."""
    capabilities = manifest["capabilities"]
    lines = [
        "# Matriz de capacidades e integração",
        "",
        "Esta matriz é gerada a partir de `config/capabilities.json` e confrontada com "
        "o OpenAPI real, as rotas TanStack e os arquivos de testes e documentação.",
        "",
        f"**Commit-base da última verificação:** `{manifest['last_verified_commit']}`",
        "",
        "## Resumo",
        "",
        "| ID | Capacidade | Frontend | API | Perfil/contexto | IA | Extensão | Snapshot | Status | Lacunas |",
        "|---|---|---|---:|---|---|---|---|---|---|",
    ]
    for capability in capabilities:
        ai = capability["ai_support"]
        prompt_summary = ", ".join(ai["prompt_ids"]) if ai["prompt_ids"] else "não"
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(capability["capability_id"]),
                    _cell(capability["label"]),
                    _code_or_dash(capability["frontend_route"]),
                    str(len(capability["api_endpoints"])),
                    _cell(capability["context_purpose"] or "sem contexto dedicado"),
                    _cell(prompt_summary),
                    _cell(capability["extension_support"]),
                    _cell(capability["snapshot_support"]),
                    _cell(capability["status"]),
                    _cell("; ".join(capability["gaps"]) or "nenhuma registrada"),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Contratos por capacidade", ""])
    for capability in capabilities:
        ai = capability["ai_support"]
        lines.extend(
            [
                f"### {capability['label']} (`{capability['capability_id']}`)",
                "",
                "| Campo | Valor verificado |",
                "|---|---|",
                _row("capability_id", f"`{capability['capability_id']}`"),
                _row("frontend_route", _code_or_dash(capability["frontend_route"])),
                _row("api_endpoints", _code_list(capability["api_endpoints"])),
                _row("backend_services", _code_list(capability["backend_services"])),
                _row("core_modules", _code_list(capability["core_modules"])),
                _row("stores", _code_list(capability["stores"])),
                _row("profile_integration", _cell(capability["profile_integration"])),
                _row("context_purpose", _code_or_dash(capability["context_purpose"])),
                _row(
                    "ai_support",
                    _cell(
                        f"enabled={str(ai['enabled']).lower()}; "
                        f"prompts={', '.join(ai['prompt_ids']) or 'nenhum'}; "
                        f"providers={', '.join(ai['providers'])}; fallback={ai['fallback']}"
                    ),
                ),
                _row("extension_support", _cell(capability["extension_support"])),
                _row("dedupe_strategy", _cell(capability["dedupe_strategy"])),
                _row("snapshot_support", _cell(capability["snapshot_support"])),
                _row("tests", _code_list(capability["tests"])),
                _row("docs", _code_list(capability["docs"])),
                _row("status", f"`{capability['status']}`"),
                _row("gaps", _cell("; ".join(capability["gaps"]) or "nenhuma registrada")),
                _row("last_verified_commit", f"`{capability['last_verified_commit']}`"),
                "",
            ]
        )
    lines.extend(
        [
            "## Como validar",
            "",
            "```bash",
            "python scripts/validate_capabilities.py",
            "python scripts/generate_integration_matrix.py --check",
            "```",
            "",
            "O modo `--check` não altera arquivos e falha quando a matriz deixa de refletir o manifesto.",
            "",
        ]
    )
    return "\n".join(lines)


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _code_or_dash(value: object) -> str:
    return f"`{_cell(value)}`" if value else "—"


def _code_list(values: list[str]) -> str:
    return "<br>".join(f"`{_cell(value)}`" for value in values) if values else "—"


def _row(field: str, value: str) -> str:
    return f"| `{field}` | {value} |"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    errors = validate_manifest(manifest)
    if errors:
        print("Não foi possível gerar a matriz: manifesto inválido.")
        for error in errors:
            print(f"- {error}")
        return 1
    expected = render_matrix(manifest)
    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.is_file() else ""
        if current != expected:
            print(f"Matriz desatualizada: {args.output.relative_to(ROOT)}")
            return 1
        print(f"Matriz atualizada: {len(manifest['capabilities'])} capacidades.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="utf-8")
    print(f"Matriz gerada: {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
