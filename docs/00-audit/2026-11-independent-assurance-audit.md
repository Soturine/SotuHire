# Auditoria independente de assurance — 2026-11

Auditoria agent-led do SotuHire com Derivanta Framework, Derivanta Engine e Assertiva, feita em
2026-11-14 sobre `main` `8ea37d7` (v2.0). Cada defeito confirmado tem um teste que falha em
`8ea37d7` e passa na branch `fix/copilot-execution-integrity`. Relatórios brutos das ferramentas
ficaram fora do repositório; aqui estão o resumo, as decisões e como reproduzir.

Documentos relacionados:

- [Dependências, advisories e PRs do Dependabot](2026-11-dependency-review.md)
- [Dogfood bidirecional e pesquisa externa](2026-11-dogfood-and-external-research.md)

## Baseline e ambiente

| Item | Valor |
| --- | --- |
| Revisão auditada | `8ea37d764861863df13ad17a1226d6f8c179c403` (worktree limpo) |
| Runtime | Windows 10, Python 3.12.6, Node 24.11.1 |
| Assertiva | 1.0.0 (tag `v1.0.0`, `d4d8d49`), venv isolado |
| Derivanta Engine | 0.1.0 (`d413e53`, Framework compatível `218761d`) |
| pytest em `8ea37d7` | 661 passed, 4 skipped (providers externos sem chave: `NOT_RUN`) |
| Vitest | 18/18 (8 arquivos) |
| Playwright Chromium | 26 passed, 9 skipped (specs de captura de release) |

Os 234 erros da primeira execução vieram do sandbox (sem acesso a `%TEMP%\pytest-of-*`) e
sumiram com `--basetemp`; o Vitest só falha quando o terminal usa a letra de unidade minúscula
(`c:\`), um problema conhecido de instâncias duplicadas no Windows. Nenhum dos dois é defeito do
produto.

## Cobertura real

| Superfície | Como foi coberta | Estado |
| --- | --- | --- |
| Copilot v2 (approval, execução, undo, Career State) | leitura semântica integral + testes de reprodução + 10 mutantes dirigidos | `VERIFIED` |
| Persistência SQLite do Copilot e das tarefas | testes contra o banco real, concorrência, injeção de falha | `VERIFIED` |
| API v2 de aprovações e `/api/v1/career/tasks` | TestClient autenticado, local e a partir do wheel instalado | `VERIFIED` |
| Extensão MV3 (service worker) | leitura de manifest/worker + harness Node adversarial | `VERIFIED` (worker); Chrome real `NOT_RUN` |
| CI, SBOM, clean install, release tooling | leitura + execução local de cada gate + clean install real | `VERIFIED` local; CI remoto `NOT_RUN` |
| Frontend `/career` | Playwright Chromium + leitura | `VERIFIED` |
| Dead code / duplicação Python | Engine (602 arquivos, 271 candidatos) + triagem dos 36 não referenciados | `PARTIAL` (duplicações não triadas) |
| Demais rotas web, i18n, acessibilidade | só a suíte E2E existente | `PARTIAL` |
| Providers Gemini/OpenAI reais | sem chaves | `BLOCKED_EXTERNAL_ACCOUNT` |
| Migrações v6→v8 com dados sintéticos, backup/restore | só a suíte existente (passa) | `PARTIAL` |
| GitHub portfolio, stores JSON legados, Lattes, Radar | não auditados semanticamente | `UNKNOWN` |

## Achados

Estados: `VERIFIED` (corrigido e provado), `CONFIRMED` (real, não corrigido), `FALSE_POSITIVE`,
`PARTIALLY_REFUTED`, `DEFERRED_WITH_RATIONALE`, `ACCEPTED_RISK`, `UNKNOWN`. "Teste" é o que falha
em `8ea37d7` e passa depois.

### Hipóteses herdadas (SH-AUD)

| ID | Resultado | Prova / decisão |
| --- | --- | --- |
| SH-AUD-001 | `VERIFIED` (P0) | `execute()` não revalidava expiry nem hash. Teste: `test_execute_revalidates_dependency_hash_after_approval`, `test_execute_rejects_expired_approved_proposal`, `test_post_approval_change_returns_conflict_without_effect` (HTTP 409, sem tarefa). |
| SH-AUD-002 | `VERIFIED` (P0) | Corrida reproduzida: 2 execuções concorrentes geravam 2 `action_executions`. Agora tudo numa transação `BEGIN IMMEDIATE`. Testes: `test_concurrent_execute_applies_effect_once`, `test_effect_and_lifecycle_are_atomic_when_recording_fails`, `test_concurrent_writer_cannot_change_state_between_check_and_effect`. |
| SH-AUD-003 | `VERIFIED` (P0) | Undo restaurava status antigo por cima de edição posterior. Agora condicional à versão. Testes: `test_undo_archive_does_not_overwrite_later_edit`, `test_undo_task_does_not_delete_task_edited_by_user`. |
| SH-AUD-004 | `VERIFIED` (P1) | Hash ignorava top oportunidades e outcomes exibidos. `test_fingerprint_changes_when_exposed_rankings_or_outcomes_change`; `test_fingerprint_ignores_unexposed_edge_metadata` prova que mudança irrelevante não invalida. |
| SH-AUD-005 | `VERIFIED` (P1) | `save_edge` devolvia `edge_id` não persistido. `test_save_edge_returns_persisted_identity`. |
| SH-AUD-006 | `VERIFIED` (P1) | Upload apontava para `sotuhire-sbom-v1.11.0.cdx.json` e `upload-artifact` só avisa. Caminho fixo, `verify_sbom.py`, `if-no-files-found: error` nos 3 uploads. |
| SH-AUD-007 | `VERIFIED` | Threat model e ADR do Copilot agora descrevem o comportamento as-built e citam os testes. |
| SH-AUD-008 | `VERIFIED` (P2) | `created` vem do `rowcount`. `test_create_task_reports_honest_creation_flag`. |
| SH-AUD-009 | `VERIFIED` (P1) | Rejeitada era devolvida para nova intenção; evidence refs fora da identidade. `test_reproposal_after_rejection_creates_new_reviewable_proposal`, `test_different_evidence_refs_are_a_different_proposal`. `reason` continua fora da identidade, por decisão. |
| SH-AUD-010 | `VERIFIED` (P2) | `due_at` agora `AwareDatetime` normalizado para UTC e com o mesmo vocabulário de `CareerTask`. |
| SH-AUD-011 | `VERIFIED` | CI agora usa `--install`; o script diz qual modo rodou. A instalação limpa real pegou uma regressão minha no SBOM antes do commit final. |
| SH-AUD-012 | `VERIFIED` (parcial) | CI roda todas as specs Chromium (eram 2 de 7); `npm audit` bloqueia em `critical`. Firefox/WebKit continuam fora do CI (custo), README corrigido. |
| SH-AUD-013 | `PARTIALLY_REFUTED` → `VERIFIED` | A doc já dizia "dependências diretas" (sem claim falso), mas o SBOM era fraco: agora 652 componentes (531 npm do lock + 121 Python transitivos) com arestas. |
| SH-AUD-014 | `PARTIALLY_REFUTED` | `build()` só retorna depois de `verify()` (schema, FKs, `integrity_check`); banco inconsistente lança `MigrationError`. `test_career_state_never_reports_healthy_for_inconsistent_database` passa já em `8ea37d7`. `rule_confidence=1.0` significa regras determinísticas — comentado no código. |
| SH-AUD-015 | `CONFIRMED` → documentado | `plan()` não interpreta a intenção e nenhum cliente web chama `/copilot/plans`. Docstring + teste de caracterização. |
| SH-AUD-016 | `CONFIRMED` (escopo) | Não há caminho modelo→tool: o Copilot não usa LLM para propor. O teste existente cobre o que existe; um teste de provider→tool só faz sentido quando esse caminho existir. |
| SH-AUD-017 | `DEFERRED_WITH_RATIONALE` | `archive_evidence` grava `stale`. Separar "arquivado" exige migração do `CHECK` e mudança de UI; registrado em próximos passos. |
| SH-AUD-018 | `UNKNOWN` | GitHub portfolio não auditado neste ciclo. |
| SH-AUD-019 | `UNKNOWN` | Stores JSON/JSONL legados não auditados neste ciclo. |
| SH-AUD-020 | `VERIFIED` | `CopilotTool.handler` nunca era preenchido nem lido; removido. |

### Achados novos (SH-NEW)

| ID | Pri. | Resultado | Descrição e prova |
| --- | --- | --- | --- |
| SH-NEW-001 | P2 | `CONFIRMED` | Todo método do `CopilotRepository` chama `ensure_database()`, que roda `PRAGMA integrity_check` e `foreign_key_check` completos; um `propose()` faz isso várias vezes. Custo cresce com o banco. Não corrigido: cachear a verificação exige invalidar em restore/migração. |
| SH-NEW-002 | P1 | `VERIFIED` | Tarefa criada pelo Copilot era gravada com `payload='{}'`; `GET /api/v1/career/tasks` passava a falhar (`ValidationError` → HTTP 500) para sempre. `test_executed_copilot_task_is_listed_by_the_career_api`. |
| SH-NEW-003 | P2 | `VERIFIED` | `due_at` gravado com offset original e comparado como texto com `now` UTC; a UI mandava `datetime-local` sem fuso. `test_overdue_detection_is_correct_for_non_utc_deadlines`. |
| SH-NEW-004 | P2 | `VERIFIED` | Lembrete ligado silenciosamente à primeira tarefa da lista. Seletor explícito + `tests/e2e/career.spec.ts`. |
| SH-NEW-005 | P2 | `CONFIRMED` | Sem lockfile Python: um ambiente válido pelo `pyproject` mantinha `pypdf 6.15.0` (29 advisories; parseia PDFs do usuário). Pisos de `pypdf` e `python-dotenv` elevados; lockfile continua pendente. |
| SH-NEW-006 | P2 | `VERIFIED` | `build_release_checksums.py` fixava nomes da v2.0; agora deriva dos manifests. |
| SH-NEW-007 | P2 | `VERIFIED` | Service worker concatenava `message.path` na URL do Companion e ignorava o `sender`: path `@host/x` mandava o token para outro host; pareamento e remoção de chave aceitos de content script. Harness `background_security_harness.js` (baseline: `tokenSentOutsideLoopback: true`). Defesa em profundidade: os chamadores atuais usam paths constantes. |
| SH-NEW-008 | P3 | `VERIFIED` | pre-commit rodava ruff 0.14.8, CI 0.16.1. Alinhado. |
| SH-NEW-009 | P1 | `VERIFIED` (parcial) | Lockfile web com 1 advisory crítica (seroval) e 6 altas que nunca falharam o CI. `npm audit fix` sem `--force`; `zod` (alta) adiada com risco. Ver [revisão de dependências](2026-11-dependency-review.md). |
| SH-NEW-010 | P2 | `VERIFIED` | Dependabot npm parado: 5 PRs de 2026-08 ocupavam o limite. Agrupamento configurado. |
| SH-NEW-011 | P2 | `VERIFIED` | Modo demo da tela Carreira: salvar tarefa, lembrete, plano, entrevista, STAR ou follow-up não aparecia na lista. Store de sessão só no modo demo. |
| SH-NEW-012 | P3 | `VERIFIED` | `wheel` em `build-system.requires` desnecessário com `setuptools>=70.1`; build não-isolado falhava sem ele. Wheel construído e qualificado num venv novo. |

## Eficácia dos testes (controles negativos)

Dez mutantes dirigidos aplicados um a um numa worktree descartável, rodando
`test_copilot_v2_integrity.py` + `test_copilot_v2_domain.py`:

| Mutante | Resultado |
| --- | --- |
| M1 remover recheck do dependency hash | morto |
| M2 remover recheck de expiry | morto |
| M3 transação diferida em vez de `BEGIN IMMEDIATE` | **sobreviveu** → teste de escritor concorrente adicionado → morto |
| M4 undo de arquivamento incondicional | morto |
| M5 `save_edge` devolve o objeto recebido | morto |
| M6 `created` sempre `True` | morto |
| M7 proposta fechada devolvida para nova intenção | morto |
| M8 payload de tarefa vazio (bug original) | morto |
| M9 fingerprint sem rankings | morto |
| M10 `due_at` sem normalização | morto |

Mutation testing completo (Cosmic Ray via Assertiva) não rodou: a ferramenta não está instalada
no projeto e a Assertiva não a instala. Estado: `NOT_RUN`.

## Código morto e duplicação

O Engine marcou 36 definições Python como não referenciadas. Todas têm exatamente uma ocorrência
no repositório (a própria definição); nenhuma é alcançada por `getattr`, `import_module`, string,
script ou frontend. Removidas por serem mortas **e** superadas:

- `local_api.security.token_is_valid` / `safe_log_label` — validador legado só de token de
  instalação; a validação real (sessão, origem, cliente) está em `modules/security/local_auth.py`;
- `modules/sources/registry.py` — registry no qual nada registra nem lê;
- `modules/alerts` — stub `should_alert()` nunca ligado (alertas seguem como roadmap);
- `CopilotTool.handler`.

Mantidas como `DECLARED_NOT_WIRED` (decisão de produto, não de limpeza): métricas de
`modules/ai/evaluation/metrics.py` citadas em `docs/04-ai/ai-cost-latency.md`; modelos de domínio
(`ProfessionalRegistration`, `AnalysisReport`) e helpers de parsers. Os 152 `DUPLICATE_TABLE` e 18
`DUPLICATE_BODY` não foram triados neste ciclo.

## Reproduzir

```bash
python -m pytest tests/test_copilot_v2_integrity.py tests/test_api_copilot_v2.py
python -m pytest tests/test_extension_reliability_runtime.py tests/test_release_tooling.py
python scripts/build_sbom.py --output dist/sotuhire-sbom.cdx.json
python scripts/verify_sbom.py dist/sotuhire-sbom.cdx.json
python scripts/verify_clean_install.py --install --skip-e2e
cd apps/web && npx playwright test --project=chromium
```

## Limites

- O CI remoto não rodou nesta branch: verde local não é verde de CI.
- Extensão não foi testada num Chrome real; o harness exercita o service worker isolado.
- Nenhum provider externo real foi chamado.
- O comparativo com outros produtos usou documentação e READMEs públicos, não uso dos produtos.
