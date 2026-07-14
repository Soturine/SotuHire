"""Generate the prompt catalog from the real PromptRegistry and source consumers."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "04-ai" / "prompt-catalog.md"
FALLBACKS = {
    "resume_extraction_v1": "Parser local de currículo",
    "job_extraction_multi_domain_v1": "Parser local de vaga",
    "domain_classification_v1": "Classificador determinístico de domínio",
    "github_repo_analysis_v2": "Analisador heurístico do repositório",
    "match_analysis_evidence_based_v1": "Match Engine determinístico",
    "ats_analysis_v1": "Revisão local de palavras-chave",
    "resume_tailor_v1": "Regras locais de adaptação segura",
    "career_advice_v1": "Orientação local baseada em evidências",
    "source_import_enrichment_v1": "Normalização determinística da importação",
    "job_radar_match_explanation_v1": "Explicação determinística de aderência",
    "job_wishlist_builder_v1": "Parser local de wishlist",
    "profile_items_extractor_v1": "Extrator local de itens de perfil",
    "profile_lattes_extractor_v1": "Parser local de Lattes",
    "public_exam_notice_extractor_v1": "Parser local de edital",
    "github_profile_analysis_v1": "Resumo local de evidências públicas",
    "portfolio_gap_analysis_v1": "Comparação determinística de lacunas",
}
STATUS_OVERRIDES = {
    "domain_classification_v1": "implementado sem fluxo integrado",
    "career_advice_v1": "implementado",
    "github_profile_analysis_v1": "implementado",
    "portfolio_gap_analysis_v1": "implementado",
}
INDIRECT_CONSUMERS = {
    "career_advice_v1": ["modules/ai/guidance.py"],
    "github_profile_analysis_v1": ["modules/ai/guidance.py"],
    "portfolio_gap_analysis_v1": ["modules/ai/guidance.py"],
}


def prompt_rows(root: Path = ROOT) -> list[dict[str, Any]]:
    """Return catalog rows derived from the registry and repository references."""
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from modules.ai.prompt_loader import initial_prompt_specs
    from modules.ai.task_registry import default_ai_task_registry

    specs = sorted(initial_prompt_specs(), key=lambda item: item.prompt_id)
    tasks = default_ai_task_registry()
    ids = {spec.prompt_id for spec in specs}
    consumers_by_id = _consumer_reference_index(
        ids,
        [root / "modules", root / "apps" / "api"],
        excluded={root / "modules" / "ai" / "prompt_loader.py"},
    )
    tests_by_id = _reference_index(
        ids,
        [root / "tests"],
        excluded={root / "tests" / "test_capability_documentation_generators.py"},
    )
    docs_by_id = _reference_index(
        ids,
        [root / "docs" / "04-ai"],
        excluded={DEFAULT_OUTPUT},
        suffixes={".md"},
    )
    rows: list[dict[str, Any]] = []
    golden_by_task = _golden_case_index(root / "tests" / "golden")
    baseline_providers = [
        provider
        for provider in ("local", "gemini", "openai")
        if (root / "benchmarks" / "baselines" / f"v1.9.7-{provider}.json").is_file()
    ]
    for spec in specs:
        task = tasks.for_prompt(spec.prompt_id)
        consumers = sorted(
            set(consumers_by_id[spec.prompt_id] + INDIRECT_CONSUMERS.get(spec.prompt_id, []))
        )
        tests = tests_by_id[spec.prompt_id]
        docs = docs_by_id[spec.prompt_id]
        if not docs:
            docs = ["docs/04-ai/prompt-registry.md"]
        rows.append(
            {
                "prompt_id": spec.prompt_id,
                "version": spec.version,
                "status": STATUS_OVERRIDES.get(
                    spec.prompt_id,
                    "implementado" if consumers else "registrado sem consumidor",
                ),
                "schema": f"{spec.output_schema.__module__}.{spec.output_schema.__name__}",
                "consumers": consumers,
                "providers": ["gemini", "openai"],
                "fallback": FALLBACKS.get(spec.prompt_id, "Não documentado"),
                "evaluation_suite": task.evaluation_suite,
                "golden_cases": golden_by_task.get(task.task_id, []),
                "last_benchmark": spec.last_benchmark or "release v1.9.7",
                "baseline_status": (
                    "available: " + ", ".join(baseline_providers)
                    if baseline_providers
                    else spec.baseline_status
                ),
                "providers_tested": baseline_providers or list(spec.providers_tested),
                "tests": tests,
                "docs": docs,
            }
        )
    return rows


def _golden_case_index(root: Path) -> dict[str, list[str]]:
    cases: dict[str, list[str]] = {}
    if not root.is_dir():
        return cases
    for path in sorted(root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        task_id = str(payload.get("task_id", ""))
        case_id = str(payload.get("case_id", ""))
        if task_id and case_id:
            cases.setdefault(task_id, []).append(case_id)
    return cases


def _consumer_reference_index(
    prompt_ids: set[str],
    roots: list[Path],
    *,
    excluded: set[Path] | None = None,
) -> dict[str, list[str]]:
    """Index executable calls by prompt id, ignoring comments and docstrings."""
    matches = {prompt_id: [] for prompt_id in prompt_ids}
    excluded_resolved = {path.resolve() for path in (excluded or set())}
    for scan_root in roots:
        if not scan_root.is_dir():
            continue
        for source in sorted(scan_root.rglob("*.py")):
            if source.resolve() in excluded_resolved:
                continue
            try:
                tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            except (SyntaxError, UnicodeDecodeError):
                continue
            used = {
                value.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                for value in ast.walk(node)
                if isinstance(value, ast.Constant) and value.value in prompt_ids
            }
            relative = source.relative_to(ROOT).as_posix()
            for prompt_id in sorted(used):
                matches[prompt_id].append(relative)
    return matches


def _reference_index(
    needles: set[str],
    roots: list[Path],
    *,
    excluded: set[Path] | None = None,
    suffixes: set[str] | None = None,
) -> dict[str, list[str]]:
    excluded_resolved = {path.resolve() for path in (excluded or set())}
    allowed_suffixes = suffixes or {".py"}
    matches = {needle: [] for needle in needles}
    for scan_root in roots:
        if not scan_root.is_dir():
            continue
        for source in sorted(scan_root.rglob("*")):
            if not source.is_file() or source.suffix not in allowed_suffixes:
                continue
            if source.resolve() in excluded_resolved:
                continue
            try:
                content = source.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            relative = source.relative_to(ROOT).as_posix()
            for needle in sorted(needles):
                if needle in content:
                    matches[needle].append(relative)
    return matches


def _consumer_references(
    prompt_id: str,
    roots: list[Path],
    *,
    excluded: set[Path] | None = None,
) -> list[str]:
    """Backward-compatible single-id wrapper for focused callers."""
    return _consumer_reference_index(
        {prompt_id},
        roots,
        excluded=excluded,
    )[prompt_id]


def _references(
    needle: str,
    roots: list[Path],
    *,
    excluded: set[Path] | None = None,
    suffixes: set[str] | None = None,
) -> list[str]:
    """Backward-compatible single-id wrapper for focused callers."""
    return _reference_index(
        {needle},
        roots,
        excluded=excluded,
        suffixes=suffixes,
    )[needle]


def render_catalog(rows: list[dict[str, Any]]) -> str:
    """Render a deterministic, implementation-backed Markdown catalog."""
    lines = [
        "# Catálogo de prompts",
        "",
        "Este catálogo é gerado do `PromptRegistry` real. Ele diferencia contratos "
        "consumidos pelo produto de contratos apenas registrados e valida schema, consumidores, "
        "providers, fallback, avaliação, baselines, testes e documentação.",
        "",
        "A IA interpreta e sugere; schemas e regras determinísticas validam a resposta. "
        "Nenhum prompt autoriza inventar formação, experiência, publicação, registro ou resultado.",
        "",
        "## Fonte de verdade",
        "",
        "- `modules/ai/prompt_loader.py` define os `PromptSpec` oficiais;",
        "- o schema Pydantic de cada spec é o contrato de saída executável;",
        "- consumidores são encontrados em chamadas Python reais, não em comentários;",
        "- testes e documentos são localizados por referência exata ao `prompt_id`;",
        "- este arquivo não contém chaves, payloads pessoais nem respostas de providers.",
        "",
        "Um arquivo em `docs/04-ai/prompts/` que não aparece na tabela pode documentar uma ideia "
        "ou capacidade futura, mas não representa um contrato registrado no runtime.",
        "",
        "## Decisão de arquitetura",
        "",
        "O produto usa prompts separados por tarefa, versionados e com schemas próprios. "
        "Não existe um prompt genérico autorizado a decidir todo o fluxo de carreira.",
        "",
        "```text",
        "entrada estruturada + evidências rastreáveis",
        "→ PromptSpec versionado",
        "→ Gemini ou OpenAI (opcional)",
        "→ validação Pydantic/JsonGuard",
        "→ fallback determinístico explícito",
        "→ revisão humana",
        "```",
        "",
        "## Regras globais",
        "",
        "Todos os prompts consumidos pelo produto devem:",
        "",
        "- retornar dados compatíveis com o schema registrado;",
        "- não inventar experiência, formação, certificação, publicação ou registro profissional;",
        "- diferenciar fato confirmado, inferência e sugestão;",
        "- preservar `source_ref` e evidências quando o fluxo as fornece;",
        "- indicar ausência de informação em vez de preencher lacunas;",
        "- reduzir confiança quando houver ambiguidade ou conflito;",
        "- manter warnings e necessidade de revisão humana;",
        "- respeitar a diferença entre requisito obrigatório, desejável e opcional;",
        "- não transformar projeto pessoal em experiência corporativa;",
        "- não transformar curso livre em graduação;",
        "- não afirmar que uma pessoa possui skill só porque a vaga a exige;",
        "- não tomar decisão crítica final nem executar candidatura;",
        "- omitir contexto sensível de providers externos sem consentimento explícito;",
        "- registrar provider/modelo solicitado e usado quando a execução é rastreada;",
        "- tornar fallback visível em metadata e warnings.",
        "",
        "## Registro verificável",
        "",
        "| prompt_id | version | status | schema | consumers | providers | fallback | evaluation_suite | golden_cases | last_benchmark | baseline_status | providers_tested | tests | docs |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _code(row["prompt_id"]),
                    _code(row["version"]),
                    _cell(row["status"]),
                    _code(row["schema"]),
                    _code_list(row["consumers"]),
                    _cell(", ".join(row["providers"])),
                    _cell(row["fallback"]),
                    _code(row["evaluation_suite"]),
                    _code_list(row["golden_cases"]),
                    _cell(row["last_benchmark"]),
                    _cell(row["baseline_status"]),
                    _cell(", ".join(row["providers_tested"])),
                    _code_list(row["tests"]),
                    _code_list(row["docs"]),
                ]
            )
            + " |"
        )

    unconsumed = [row for row in rows if not row["consumers"]]
    lines.extend(
        [
            "",
            "## Como interpretar o status",
            "",
            "- `implementado`: existe ao menos uma chamada executável que referencia o prompt;",
            "- `implementado sem fluxo integrado`: há serviço executável, mas nenhuma rota/feature o invoca;",
            "- `registrado sem consumidor`: o contrato está no registry, mas nenhum fluxo o chama;",
            "- a presença no registry não prova que todas as telas usam o resultado;",
            "- a coluna `tests` mostra referências existentes, não uma garantia automática de cobertura total.",
            "",
            "## Contratos sem consumidor",
            "",
        ]
    )
    if unconsumed:
        lines.extend(
            f"- `{row['prompt_id']}` está registrado, mas não é chamado por nenhum módulo ou serviço."
            for row in unconsumed
        )
    else:
        lines.append("Todos os contratos registrados possuem ao menos um consumidor no código.")

    lines.extend(
        [
            "",
            "## Envelope de entrada recomendado",
            "",
            "Nem todos os prompts usam todos os campos, mas integrações novas devem preferir "
            "contexto estruturado e mínimo em vez de concatenar dados indiscriminadamente.",
            "",
            "```json",
            "{",
            '  "prompt_id": "string",',
            '  "prompt_version": "string",',
            '  "language": "pt-BR",',
            '  "analysis_mode": "fast | standard | deep",',
            '  "user_goal": "string | null",',
            '  "candidate_profile": "object | null",',
            '  "job_post": "object | null",',
            '  "resume_text": "string | null",',
            '  "job_text": "string | null",',
            '  "career_context": "object | null",',
            '  "source_refs": [],',
            '  "constraints": "object | null"',
            "}",
            "```",
            "",
            "O contexto enviado deve ser limitado ao propósito da análise. O Perfil Universal "
            "completo não deve ser anexado a toda chamada por padrão.",
            "",
            "## Envelope de saída recomendado",
            "",
            "O schema específico é soberano. Quando fizer sentido para o fluxo, ele deve expor "
            "também os sinais de auditoria abaixo:",
            "",
            "```json",
            "{",
            '  "result": {},',
            '  "confidence": 0.0,',
            '  "needs_human_review": true,',
            '  "warnings": [],',
            '  "evidence_used": [],',
            '  "source_refs": [],',
            '  "missing_information": [],',
            '  "unsupported_claims": []',
            "}",
            "```",
            "",
            "Campos ausentes não devem ser confundidos com campos não analisados. Uma resposta "
            "válida no JSON, mas incompatível com as evidências, ainda deve ser rejeitada ou "
            "marcada para revisão.",
            "",
            "## Metadados de execução",
            "",
            "Fluxos rastreados devem manter, quando disponíveis:",
            "",
            "- `run_id`, `feature`, `prompt_id` e `prompt_version`;",
            "- `provider_requested`, `provider_used`, `model_requested` e `model_used`;",
            "- `analysis_mode`, `fallback_used` e `fallback_reason`;",
            "- `schema_valid`, `latency_ms`, `token_usage` e `estimated_cost`;",
            "- `input_hash`, `context_sources`, `source_refs` e `evidence_used`;",
            "- `warnings`, `needs_user_review` e `created_at`.",
            "",
            "Segredos, cabeçalhos de autenticação e conteúdo sensível não pertencem ao trace.",
            "",
            "## Política de fallback",
            "",
            "O fallback é uma decisão de produto, não apenas tratamento de exceção:",
            "",
            "1. preserve a entrada original e o resultado determinístico local;",
            "2. tente o provider somente quando o recurso e a permissão estiverem ativos;",
            "3. valide a saída estruturada antes de mesclar qualquer campo;",
            "4. ao falhar, use o resultado local sem ocultar `fallback_used`;",
            "5. informe um motivo seguro, sem incluir chave, payload integral ou traceback sensível;",
            "6. mantenha a decisão final sob revisão da pessoa usuária.",
            "",
            "Quando não existe fallback seguro, o fluxo deve retornar indisponibilidade clara em "
            "vez de fabricar uma resposta aparentemente completa.",
            "",
            "## Providers e fallback",
            "",
            "Os mesmos `PromptSpec` estruturados podem ser executados pelos adapters Gemini e "
            "OpenAI. O provider local não consome esses prompts: ele representa o caminho "
            "determinístico indicado na coluna `fallback`. Falhas externas devem aparecer nos "
            "metadados da análise e nunca ser silenciosas.",
            "",
            "## Multiárea e linguagem",
            "",
            "Os contratos devem funcionar para tecnologia, engenharias, saúde, direito, educação, "
            "pesquisa, artes, design, administração, turismo, cursos técnicos e transição de "
            "carreira. Exemplos e schemas não podem pressupor que todo portfólio é software ou "
            "que toda evidência profissional vem de emprego formal.",
            "",
            "## Quando não usar IA",
            "",
            "Não é necessário chamar um provider para:",
            "",
            "- CRUD, mudança de estágio ou cálculo de métricas do Tracker;",
            "- validação de checksum, backup, restore ou migração de schema;",
            "- deduplicação por identificador forte, DOI, ORCID ou URL canônica;",
            "- aplicação de regras de segurança e bloqueios anti-invenção;",
            "- operações que já possuem resultado determinístico suficiente;",
            "- qualquer ação automática de candidatura ou inscrição, que está fora de escopo.",
            "",
            "A IA também não deve ser usada para confirmar sozinha um ProfileItem, declarar que "
            "um requisito regulatório foi atendido ou substituir leitura oficial de edital.",
            "",
            "## Revisão humana",
            "",
            "A interface deve solicitar revisão quando houver baixa confiança, evidência conflitante, "
            "claim sem source_ref, dado sensível, requisito regulado, mudança material no currículo "
            "ou fallback. Aceite e rejeição humana são sinais de avaliação; não são autorização "
            "para aprender ou publicar dados pessoais fora do ambiente local.",
            "",
            "## Avaliação associada",
            "",
            "Prompts consumidos devem ser avaliados com fixtures multiárea e, quando aplicável:",
            "",
            "- validade de schema e acurácia de extração de campos;",
            "- precisão/recall de evidências;",
            "- taxa de claims sem suporte e alucinação;",
            "- calibração de confiança e taxa de fallback;",
            "- latência, tokens, custo estimado e concordância entre providers;",
            "- aceitação/rejeição humana e precisão de deduplicação.",
            "",
            "Testes externos são opt-in. O CI padrão usa fakes/mocks e não depende de chaves reais.",
            "",
            "## Regras de manutenção",
            "",
            "- altere o `PromptSpec` e seu schema de saída de forma versionada;",
            "- mantenha ao menos um teste com provider fake para prompts consumidos;",
            "- preserve evidências, warnings e necessidade de revisão humana;",
            "- não registre chaves, payloads sensíveis ou conteúdo pessoal neste catálogo;",
            "- regenere e confira este arquivo após incluir ou remover prompts.",
            "",
            "Um prompt só deve ser tratado como pronto quando possui objetivo claro, versão, "
            "schema, consumidor, fallback explícito, teste e documentação coerente. Alterações "
            "incompatíveis exigem nova versão do contrato.",
            "",
            "### Checklist de alteração",
            "",
            "1. confirme se a mudança altera apenas texto ou também o contrato;",
            "2. atualize versão e schema quando houver incompatibilidade;",
            "3. ajuste consumidores e fixtures com provider fake;",
            "4. valide o caminho de fallback e os warnings;",
            "5. verifique que evidências/source_refs continuam preservados;",
            "6. gere novamente este catálogo e execute `--check`;",
            "7. registre mudanças de produto no CHANGELOG, não neste catálogo atemporal.",
            "",
            "## Validação",
            "",
            "```bash",
            "python scripts/generate_prompt_catalog.py",
            "python scripts/generate_prompt_catalog.py --check",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _code(value: object) -> str:
    return f"`{_cell(value)}`"


def _code_list(values: list[str]) -> str:
    return "<br>".join(_code(value) for value in values) if values else "—"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rows = prompt_rows()
    expected = render_catalog(rows)
    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.is_file() else ""
        if current != expected:
            print(f"Catálogo de prompts desatualizado: {args.output.relative_to(ROOT)}")
            return 1
        print(f"Catálogo atualizado: {len(rows)} prompts registrados.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="utf-8")
    print(f"Catálogo gerado: {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
