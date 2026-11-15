# Estado para retomada (auditoria 2026-11 e redesign v5)

Documento curto para a próxima sessão continuar sem reauditar. Detalhe e evidência: [ledger](2026-11-checkpoint-ledger.md) e [matriz](2026-11-completion-matrix.md).

## Onde está

| Repositório | Branch | PR | Observação |
| --- | --- | --- | --- |
| SotuHire | `fix/copilot-execution-integrity` | [#57](https://github.com/Soturine/SotuHire/pull/57) | checkpoints até CP-CI01 (contrato OpenAPI estável, cache do `ensure_database`, DAST com sessão) |
| Derivanta | `feat/approval-consumption-and-required-artifacts` | [#12](https://github.com/Soturine/Derivanta/pull/12) | links corrigidos (`db2dcc7`); `Documentation integrity` falha na estrutura das evals, como na `main` |
| Derivanta-Engine | `feat/ci-workflow-checks` | [#4](https://github.com/Soturine/Derivanta-Engine/pull/4) | workflow não roda em PR; CI disparado manualmente |
| Assertiva | `fix/precommit-hook-tool-identity` | [#10](https://github.com/Soturine/Assertiva/pull/10) | `f1dec58`: núcleo volta a não nomear ferramentas |

O resultado do CI de cada PR está no ledger (seção "CP-CI01"). Nenhum merge, tag ou release foi feito; as PRs do Dependabot supersedidas devem ser fechadas só depois do merge.

## Como reproduzir as provas

| Prova | Comando (a partir da raiz, Windows) |
| --- | --- |
| Backend | `python -m pytest -q --basetemp=<dir>` (definir `TEMP`/`TMP` para um diretório gravável) |
| Frontend unitário | `cd apps/web; npx vitest run` (cwd com `C:` maiúsculo no Windows) |
| E2E por navegador | `npx playwright test --project=chromium` (Firefox: `--workers=2`) |
| API real | `SOTUHIRE_DATA_DIR=<vazio> SOTUHIRE_PAIRING_BOOTSTRAP=<x> python scripts/run_api.py`; depois `REAL_API_BOOTSTRAP=<x> npx playwright test tests/e2e/real-api-shell.spec.ts` |
| Capturas de UX | `CAPTURE_UX=1 CAPTURE_UX_DIR=<dir> CAPTURE_UX_VIEWPORTS=desktop,tablet,mobile,small CAPTURE_UX_THEMES=light,dark npx playwright test tests/e2e/ux-baseline.spec.ts tests/e2e/ux-states.spec.ts`; galeria: `python scripts/build_ux_gallery.py` |
| Web Vitals | `npx vite build; npx vite preview --port 4173 --strictPort; node scripts/measure-vitals.mjs` |
| Mutantes de UI | `cd apps/web; python scripts/ui-mutants.py --out <json>` (nada mais editando `src/`) |
| Contrato cliente × API | `python scripts/export_openapi.py` quando a API mudar; o pytest acusa cópia velha |
| Extensão no Chromium | `python scripts/verify_extension_in_chromium.py` |
| DAST | API rodando num `SOTUHIRE_DATA_DIR` descartável + `python scripts/dast_local_api.py --bootstrap <x>` (cria um backup; nunca contra dados reais) |
| Cache do banco | `python -m pytest tests/test_ensure_database_cache.py` |

## Próximos passos, em ordem de valor

1. Revisar as PRs e decidir o merge só com checks verdes. Derivanta #12: o dono decide sobre os 17 casos de eval que falham a checagem de estrutura (também na `main`). Engine #4: decidir se o workflow deve rodar em `pull_request`.
2. SH-NEW-005 (lockfile Python) e SH-NEW-009 (`zod` adiada): ver C03.
3. C06: retirada do `LocalStore` (Application Lab, Local API, Radar, fontes, Tracker) com backup e rollback; o round-trip de `tests/test_data_round_trip.py` serve de base.
4. Verificar as escritas que montam literais na tela contra o contrato (o teste atual cobre as 10 que usam objetos de domínio).
5. Tradução da interface das telas de produto (hoje só shell, busca, Cockpit, Copilot e Aprovações mudam de idioma).
6. C10: ligar `plan(intent)` a um consumidor real ou decidir retirá-lo; C02 (SH-AUD-018/019), C07, C08, C27.
7. Application Lab: recomposição completa (o CP-UX04 só tratou orientação × mudança e o estado da sessão).
8. Leitor de tela: rodada manual com NVDA (não disponível nesta sessão).
