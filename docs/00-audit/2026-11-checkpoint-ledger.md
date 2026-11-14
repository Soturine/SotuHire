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

## Ativação das ferramentas (adendo v4)

| Instrumento | Estado nesta sessão | Como foi usado |
| --- | --- | --- |
| Skill Assertiva (`SKILL.md` 1.0.0) | `LOADED_BY_READ`: lida integralmente; não registrada como Skill do Claude Code (a lista de Skills é fixada no início da sessão) | laço investigar → evidência → correlacionar; vocabulário OBSERVED/DECLARED/INFERRED/UNKNOWN; nunca `--approve`; auditoria só em cópia congelada |
| Skill Derivanta (Engine adapter) e Skill Derivanta (Framework) | `LOADED_BY_READ` | MCP antes de CLI; `truncated` é digest; exit 6 é indecidível; "achar o que nenhuma ferramenta nomeou" |
| Derivanta Engine MCP | `MCP_INVOKED` por cliente MCP oficial via stdio (o servidor não está configurado na sessão; ligar exige reiniciar) | `derivanta_inspect`: digest de 50 achados (`truncated: true`) ⊂ 218 da CLI; com `max_findings` o relatório completo tem as mesmas 218 impressões digitais da CLI |
| Derivanta Engine CLI | `CLI_AGENT_OPERATED` | `inspect --maintainability` em dois clones e `compare` |
| Assertiva CLI | `--execute` e `--execute --mutate` (Cosmic Ray 8.9.0 instalado no venv isolado, não no projeto) | baseline/after de mutação; reteste cruzado da correção da própria Assertiva |

## CP-04 — afirmações de credencial no aceite (SH-NEW-014), dogfood A→E

| Campo | Registro |
| --- | --- |
| Pergunta (A) | No Application Lab, dá para aceitar sugestão que afirma registro ou pós-graduação ausente de toda evidência confirmada? Oráculo: o aceite falha e a sugestão fica pendente. |
| Execução (B) | teste que falha em `ca66c53` (aceite de "registro ativo no CRM e doutorado" passou); controles (credencial já no currículo, texto sem credencial) passam |
| Contraprova (C) | Assertiva `--execute --mutate modules/ai/claim_validation.py`: antes 26 mutantes, 14 mortos, 12 sobreviventes; 11 são equivalentes (anotação `BaseModel \| dict` vira string com `from __future__ import annotations`), 1 real (alias `statement` sem teste) |
| Correção (D) | `4b5bbe1`: `credential_claims`/`unsupported_credential_claims` (26 conselhos e registros + pós-graduação) ligados ao aceite; teste do alias `statement` mata o sobrevivente real (mutante manual: falha com a mutação) |
| Reteste (E) | depois: 30 mutantes, 18 mortos; os 4 mutantes novos (detector) mortos; restam os 11 equivalentes e o do alias (antes do teste novo) |
| Achados nas ferramentas | **Assertiva**: erros de coleta por ambiente não preparado lidos como falha de produto → corrigido em `fee2c44`; a primeira versão quebrava toda auditoria (dataclass congelada) e foi pega pelo reteste cruzado. **Engine**: `DIFFERENT_TARGET` com worktree/export não é bug (limite documentado, ADR-0006); a lacuna era de orientação no Skill → `35f9951`. **Framework**: controle só alcançado por testes é proteção não ligada, não código morto → `7e1ecba`. |
| Disposição de leads meus refutados | "revision null é bug do Engine" → FALSE_POSITIVE (limite de segurança intencional) |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, triagem) |
| `FINAL_VERDICT` | `AGENT_LED_VERIFIED` (classificação interna deste projeto) |

## CP-05 — consumidores alcançáveis no catálogo (SH-NEW-015) e segunda camada de código morto

- `0ab4e68`. O gerador do catálogo de prompts só conta consumidor importado por produção; três prompts
  deixaram de constar como implementados. Remoções confirmadas por dois instrumentos (grafo de imports e
  `compare` do Engine entre clones).
- `CHANGELOG_GATE: PASS` · `DOCS_GATE: PASS` · pytest 780 passed / 4 skipped.

## CP-EXT01 — provider Anthropic (Claude Haiku 5.5)

| Campo | Registro |
| --- | --- |
| Fonte primária | platform.claude.com/docs/en/models/haiku-5-5/overview (consultada em 2026-11-14): `claude-haiku-5-5`, sem `temperature`/`top_p`/`top_k`; SDK `anthropic` 2.8.0 inspecionado (`messages.parse` sem parâmetros de amostragem) |
| Implementação | adapter isolado, extra `ai`, fábrica e `ANTHROPIC_*` no backend, catálogo local, API e tela de configurações |
| Achados no caminho | o schema de atualização gravava o modelo do Gemini para qualquer provider (teste falha antes, passa depois); `.env.example` com 20 de 24 variáveis sem leitura no código (SH-NEW-016); a fixture com formato de chave quebraria o secret scan do CI (corrigida antes do commit) |
| Evidência | `MOCK_PASS`: 19 testes de contrato, teste da API de configurações, E2E Chromium da tela; real `BLOCKED_EXTERNAL_CREDENTIALS` |
| Testes | pytest 802 passed / 4 skipped; Vitest 18; Playwright das specs de configurações; tsc 0; pyright 0; secret scan e mkdocs --strict passam |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, provider-strategy, README, setup, `.env.example`) |

### Hashes dos relatórios brutos do CP-04 (fora do repositório)

| Relatório | SHA-256 |
| --- | --- |
| MCP inspect (digest) | `6017acb80c4b810f9c9eda67459e3c2edd9f5320583d18f826cd3ab2072abe46` |
| MCP inspect (completo) | `64999e55140ff063968ebf9b4d3baf994c4912198e94dac80e47d9a8eb99a3c4` |
| CLI inspect | `3cd354753010cd476fd17a717c433c6a2c2ecfd7c31e95842f087b942281379a` |
| compare entre clones | `558f13c33e57efae4c8d2df6570a16b4a8dc53658e7dcf26aac6910e051a96db` |
| mutação antes | `4e87cdb6958c8d8e58759660e61210a013ef486c62b6f927b6ce6de674ac45cc` |
| mutação depois | `6a09b16ecff534d062793e26dd80329cfe43c5213037bfd1d9a8615278a1752f` |
| reteste da atribuição | `9d993536c74451be7d221334fe78563cb537f3ce54099ede5513f0fbf8457c82` |

## CP-FE00 / CP-DATA01 / CP-FE01a — evidência de UX, autoridade dos dados e acessibilidade

| Campo | Registro |
| --- | --- |
| Pergunta | O que a pessoa informa uma vez chega ao currículo sem redigitação? A interface é operável por tecnologia assistiva? |
| Baseline | `86ea930` (spec de captura, axe dev-only); capturas antes em `8b9e82a`: 20 críticos, 309 sérios, 0 estouro, 0 erro de console |
| Achados | primeiro uso do Resume Studio era tela de erro (o modo demo escondia); currículo não derivava do Perfil; rascunho do navegador vencia o servidor; terceira cópia da regra de confirmação em `ResumeEntry`; cores semânticas usadas como texto |
| Correções | projeção Perfil → Mestre com revisão; onboarding; painel de atualizações; precedência de rascunho; tokens `-strong` calculados e calibrados contra o axe; rótulos |
| Testes | pytest 805 passed / 4 skipped; Vitest 22; Chromium E2E 29 passed, 0 failed (53 skipped são capturas condicionadas); E2E novo falha com a rota anterior (controle negativo válido; o primeiro controle saiu inconclusivo por gravação em UTF-16 e foi refeito) |
| Depois | 0 críticos, 0 sérios, 0 estouro, 0 erro de console nas 22 rotas × 2 viewports |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (mapa de autoridade, documento de UX com pares antes/depois, CHANGELOG, mkdocs) |
| Pendente | redesign visual amplo; componente `Field`; leitor de tela; edição de fatos já projetados; retirada de `LocalStore` |

## Ferramentas (repositórios donos)

| Repo | Branch | SHA | Push | Testes |
| --- | --- | --- | --- | --- |
| Derivanta | `feat/approval-consumption-and-required-artifacts` | `7e1ecba` | confirmado | `scripts/tests` 26 passed; checagem de links igual à de antes (7 itens pré-existentes) |
| Derivanta-Engine | `feat/ci-workflow-checks` | `35f9951` | confirmado | suíte 951 passed, 5 skipped |
| Assertiva | `fix/precommit-hook-tool-identity` | `fee2c44` | confirmado | suítes relacionadas 234 passed; suíte completa em `b0dec09`: 1.332 passed + 1 falha só do ambiente (`%TEMP%`); suíte completa em `fee2c44` em execução |