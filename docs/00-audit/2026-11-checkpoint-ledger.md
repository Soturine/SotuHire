# Ledger de checkpoints — 2026-11

Registro vivo dos checkpoints (CP) da [auditoria de 2026-11](2026-11-independent-assurance-audit.md).
Cada CP fecha com código, testes e documentação no mesmo push. CI remoto fica para o gate final
(orçamento de 3.000 min/mês de GitHub Actions): os pushes vão para branches sem PR aberta, e
nenhum workflow dos quatro repositórios dispara em push fora de `main`.

Branch: `fix/copilot-execution-integrity`. Base: `main` `8ea37d7`.

## Reconciliação retroativa (commits anteriores a este ledger)

| CP | Commits | Comportamento alterado | CHANGELOG | Docs | Validação local |
| --- | --- | --- | --- | --- | --- |
| CP-00 integridade do Copilot, extensão, CI/SBOM | `b3b3e76`…`9fd4f97` (14) | aprovação revalidada no efeito, undo condicional, listagem de tarefas, `due_at` UTC, sender da extensão, SBOM transitivo, gates de CI | **faltava**; entrada `Unreleased` criada neste CP (Segurança, Corrigido, Alterado) | threat model, `human-approved-copilot.md`, `ci-cd.md`, README, ledger de findings, revisão de dependências e dogfood já no commit `81acf0e` | pytest 690/4 skip, Vitest 18, Chromium 27/9 skip, clean install, mkdocs strict |
| CP-01 um manifesto de dependências | `3f46550` | Streamlit e pandas fora da instalação padrão; extras; licença SPDX; `docs/requirements` removido | **faltava**; `Alterado` e `Removido` | setup, commands, guias de IA e captura, `scripts/README.md`; README e roadmap neste CP | ruff, 100 testes impactados, wheel construído sem aviso |
| CP-02 código morto e duplicação | `4000993` `b6f2160` `38ec405` `81b748a` `caf26ac` `cf9a931` `00f8a98` | checagem de credenciais única; alias `import-lattes` deprecated; remoções sem consumidor | **faltava**; `Segurança`, `Obsoleto`, `Removido` | arquitetura de storage, matriz de capacidades, `ai-cost-latency.md`, `apps/web/README.md`; triagem por candidato neste CP | pytest 764/4 skip, pyright 0, catálogos e capabilities válidos |

## CP-03 — reconciliação documental e últimos vocabulários duplicados

- Motivo: o CHANGELOG não registrava nada desde a v2.0; faltavam a triagem por candidato e o
  ledger. Três listas ainda repetiam vocabulários do schema de extração de vaga, a lista de stores
  legados e as tags ativas de HTML.
- Código: `modules/ai/schemas/job_extraction.py` passa a dono de `JobWorkModel`,
  `JobContractType` e `JobSeniorityLevel`; o extrator usa `get_args`; `storage/health.py` usa
  `legacy_migration.LEGACY_PATHS`; `document_ingestion._ACTIVE_TAGS`.
- Docs: `CHANGELOG.md` (`Unreleased`), `README.md` (extras), `docs/01-product/roadmap.md`,
  [triagem](2026-11-dead-dedupe-triage.md), este ledger, `mkdocs.yml`.
- `CHANGELOG_GATE: PASS` · `DOCS_GATE: PASS` (`mkdocs build --strict` sem aviso).
- Testes (Windows 10, Python 3.12.6, Node 24.11.1): pytest 766 passed / 4 skipped (opt-in de providers
  externos sem chave); ruff check e format; pyright 0 erros; `tsc --noEmit` 0; ESLint do blob
  commitado de `sources.tsx` 0 erros (o checkout local com `core.autocrlf=true` acusa só `␍`).

## Ferramentas (repositórios donos)

| Repo | Branch | SHA | Push | Testes |
| --- | --- | --- | --- | --- |
| Derivanta | `feat/approval-consumption-and-required-artifacts` | `767b55f` | confirmado | `scripts/tests` 26 passed |
| Derivanta-Engine | `feat/ci-workflow-checks` | `f571a13` | confirmado | suíte 951 passed |
| Assertiva | `fix/precommit-hook-tool-identity` | `b0dec09` | confirmado | suíte completa 1.332 passed, 32 skipped, 1 failed: `test_installed_artifact_context` roda uma suíte interna que não herda `--basetemp` e bate no `%TEMP%` bloqueado do sandbox; com `TEMP` no scratchpad passa (2/2). `BLOCKED_ENVIRONMENT`, não produto |
