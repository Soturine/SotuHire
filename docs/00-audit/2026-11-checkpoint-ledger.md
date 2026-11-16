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

## CP-DEP01 e CP-CX01 — Dependabot integrado; triagem de alta complexidade

- `6583492`: atualizações revisadas integradas (pins conferidos contra as tags); `globals` 17 adiado.
  Detalhe em [dependências](2026-11-dependency-review.md).
- CP-CX01: 68 candidatos `HIGH_COMPLEXITY` com decisão (ver [triagem](2026-11-dead-dedupe-triage.md)).
  `LocalCompanionApp.handle` (fronteira de autenticação, 34 caminhos) virou tabela de rotas, 21
  caminhos, com teste de caracterização escrito antes (32 casos; o de 405 falha no código antigo). O
  próprio ciclo tinha introduzido 3 funções acima do limiar; 2 foram simplificadas.
- `CHANGELOG_GATE: PASS` · `DOCS_GATE: PASS` · pytest 837 passed / 4 skipped.

## CP-SEC02 — fronteira da Companion e idempotência do Currículo Mestre

| Campo | Registro |
| --- | --- |
| Pergunta | Conteúdo de quem não se autenticou é interpretado? O teste da fronteira acompanha a tabela? Aplicar fatos do Perfil é idempotente e seguro sob concorrência? |
| Reprodução | controle negativo contra `f55b1d4`: 45 falhas no teste da fronteira (422 sem credencial com corpo inválido ou não UTF-8; `AttributeError` com `[]` em `/pairing/complete`); socket real 400 em vez de 401; 5 de 6 testes de idempotência falham (3 entradas para 3 IDs repetidos, 422 no retry, gravação perdida) |
| Correção | `handle()` autentica antes de decodificar; servidor só lê bytes; `PUBLIC_PATHS` + `AUTHENTICATED_ROUTES` como registro único; `apply_profile_updates` deduplica e ignora o que já está no Mestre; `save_master_resume(expected_updated_at=…)` sob `BEGIN IMMEDIATE`, 409 na API |
| Achados | SH-NEW-017, 018, 019 |
| Pendente | variantes ainda em "última gravação vence"; reimportação do mesmo arquivo é upsert sem aviso |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, mapa de autoridade, segurança da Local API, ledger de findings) |

## CP-UX00 — baseline do redesign (adendo v5)

| Campo | Registro |
| --- | --- |
| SHA do app medido | `459ffa9` (interface igual à de `f55b1d4`) |
| Cobertura | 250 telas + 10 estados; Chromium, demo, reduced-motion |
| Achados de experiência | navegação por módulo com 23 links; busca com 4 telas em inglês e 0 resultados para "currículo"/"vaga"; zeros falsos com a API fora do ar; título truncado no mobile; ações em inglês na interface pt-BR; tema escuro com 28 nós de contraste por largura (nunca medido) |
| Decisão | direção "dossiê de carreira" (alternativas no documento de direção), ADR 006 |
| Não é | redesign: nenhuma tela mudou neste checkpoint |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS |

## CP-UX01 — design system, shell por jornada, busca; API Real consertada

| Campo | Registro |
| --- | --- |
| Hipótese | navegação por módulo, busca que não acha telas e zeros falsos tornam o produto difícil e pouco confiável; identidade genérica |
| Mudança | tokens e fontes próprios, marca, registro único de telas por jornada, shell desktop/tablet/mobile, busca única, estados compartilhados, Cockpit; tema escuro sem `-foreground` sobre tons |
| Achados no caminho | SH-NEW-020 (v2 nunca saía do navegador em API Real), SH-NEW-021 (401 sem CORS impedia o pareamento web), SH-NEW-022 (falso verde no E2E do Radar); "Revisar" do Cockpit sempre levava a Aprovações; seleção da busca não acompanhava o melhor resultado (pego pelo E2E novo) |
| Testes | Vitest 29/29; Chromium E2E 34 passed, 0 failed (70 skipped: capturas e API real condicionadas); `journey-shell.spec.ts` (5) escrito para falhar na versão anterior; unitário do pareamento v2 falha no código anterior; pytest do middleware 11/11 (o teste novo falha antes); jornada contra a API real em diretório sintético passa |
| Medidas | escuro 28 → 0 nós axe por largura; claro 0 → 0; busca 0 → 4/4/3; JS +6,8 KB gzip, CSS +2,1 KB gzip, fontes 198 KB |
| Não é | redesign das telas Perfil, Resume Studio, Radar, Tracker, Lab, Copilot e Configurações (só tokens e shell chegaram a elas) |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, direção de design, galeria, ADR 006, findings) |

## CP-UX01B — correção visual do redesign (adendo v5.2)

| Campo | Registro |
| --- | --- |
| Hipótese | o CP-UX01 acertou estrutura e errou superfície: barra e conteúdo no mesmo bege, sem cor nem profundidade; recuperar contraste e personalidade da baseline sem perder o comportamento novo |
| Mudança | tokens híbridos (barra marinho como ilha escura, hierarquia de superfícies, petróleo, gradiente só no hero e na ação principal), Cockpit recomposto, `StatCard`/`SectionCard`/`ScoreRing` atualizados, marca e favicon |
| Achados no caminho | retry de 4xx atrasava o primeiro uso do Resume Studio em ~7 s e tornava o E2E instável (2/3 falhas sob carga; 75/75 depois); v2 perdia o status HTTP; setores da pizza sem nome (`svg-img-alt`, dependente de tempo) |
| Testes | Vitest 32/32 (3 novos de retry); Chromium E2E 33 passed + o instável investigado (repetição 3× de 3 specs: 75/75); captura 200 telas + 10 estados: 0 nós axe, 0 estouro, 0 erro de console |
| Medidas | JS +1,0 KB e CSS +0,8 KB gzip contra `739023c`, mesmo método |
| Não é | redesign das demais telas (segue em CP-UX02…05) |
| Commit | `81aba70` (push confirmado com `ls-remote`) |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, direção de design, ADR 006, galeria `2026-11-v5-ux01b`) |

## CP-UX02 — Perfil, Resume Studio, primeira visita; variantes versionadas

| Campo | Registro |
| --- | --- |
| Hipótese | Perfil e Resume Studio eram listas longas de formulários; dados informados uma vez podiam divergir entre Perfil, Mestre e variantes sem sinal; 8 etapas antes da primeira tela |
| Mudança | composição nova das duas telas, `Field` compartilhado, onboarding em 2 etapas; backend: variantes com `expected_updated_at` (409), lista e atualização a pedido de fatos alterados no Perfil |
| Achados no caminho | SH-NEW-024…029 (ver auditoria); dois E2E instáveis investigados até a causa (retry de 4xx, hidratação tardia das configurações de IA), nenhum mascarado |
| Testes | pytest 941 passed, 4 skipped (providers externos sem chave); 6 novos de reconciliação, o módulo nem importa no código anterior; Vitest 35/35; Chromium E2E 39 passed, 0 failed, 71 skipped (capturas e API real condicionadas); API real: 2 jornadas passam (fato → Mestre → autosave → JSON/PDF → edição reconciliada) |
| Medidas | 0 nós axe, 0 estouro, 0 erro de console nas 8 combinações; onboarding 8 → 2 etapas |
| Não é | Radar, Tracker, Lab, Copilot e Configurações recompostos (CP-UX03/04); reimportação do mesmo arquivo continua upsert sem aviso |
| Commit | `2ec7fe2` (push confirmado com `ls-remote`) |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, mapa de autoridade, auditoria, galeria `2026-11-v5-ux02`, direção de design) |

## CP-UX03 — Radar, Fontes, Tracker; busca nos dados

| Campo | Registro |
| --- | --- |
| Hipótese | as telas de oportunidades repetiam 4 cartões genéricos, o Tracker não mostrava o funil nem servia no celular, e a busca de dados dependia de acento e ignorava Perfil e candidaturas |
| Mudança | painel de estado do Radar, funil e cartões do Tracker, navegação de Fontes; busca de dados nova (`modules/copilot_v2/search.py`) |
| Achados no caminho | SH-NEW-030, 031; o E2E de arraste do Kanban falhou com a mudança: o centro do cartão passou a cair no `select` e o destino fora da tela; as duas causas confirmadas por sonda e teste com o arquivo anterior |
| Testes | pytest 945 passed, 4 skipped; 4 testes de busca (o de API falha no código anterior); Vitest 36/36 (novo: corpo do Tracker só com campos do contrato); Chromium E2E 43 passed, 0 failed, 72 skipped; spec novo `opportunities-ux.spec.ts` (4) |
| Medidas | 0 nós axe, 0 estouro, 0 erro de console nas 8 combinações |
| API real | 3 jornadas em diretório sintético passam; a do Tracker (criar → achar pela busca sem acento → mudar status → recarregar) achou SH-NEW-032 |
| Não é | comparação lado a lado de vagas; alertas de duplicatas redesenhados; verificação sistemática dos ~30 corpos de requisição do cliente contra os schemas (pendência para o dogfood de contrato) |
| Commit | `9bff13a` (push confirmado com `ls-remote`) |
| Desvio de processo | a checagem de formatação antes do commit rodou como `prettier --check … | tail -1`, que engole o código de saída; o commit seguiu com um aviso. Conferido depois sobre o blob commitado (`git show HEAD:… | prettier --check`): exit 0, o aviso era só CRLF da cópia de trabalho. Desde então as checagens imprimem o código de saída e não passam por pipe. |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, auditoria, galeria `2026-11-v5-ux03`) |

## CP-UX04 — Aprovações, Copilot, Lab e Configurações

| Campo | Registro |
| --- | --- |
| Hipótese | o controle humano existia, mas a tela não o tornava legível: rótulos crus, JSON, falhas mudas, botões que no demo não faziam nada |
| Mudança | Aprovações reescrita; drawer do Copilot com `lib/recommendations.ts` compartilhado com o Cockpit; demo com estado e máquina de estados; Lab (orientação × mudança, estado da sessão); Configurações (destino do texto, capacidades recolhidas, `aria-pressed`) |
| Intertravamentos | nenhum relaxado: "Aprovar tudo" continua inexistente; aprovar não executa; afirmação sem evidência continua recusada pelo serviço (confirmado no código) |
| Testes | Vitest 36/36; Chromium E2E 48 passed, 0 failed, 72 skipped; `control-ux.spec.ts` (6) cobre ciclo aprovar → executar → desfazer, transição recusada (409), destino do texto, Copilot → fila, orientação no Lab |
| IA externa | `BLOCKED_EXTERNAL_CREDENTIALS`: nenhuma chamada paga feita |
| Medidas | 0 nós axe, 0 estouro, 0 erro de console nas 8 combinações |
| Não é | recomposição completa do Application Lab (1.445 linhas; só os pontos acima); Copilot conversacional |
| Commit | `94539b2` (push confirmado com `ls-remote`) |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, auditoria, galeria `2026-11-v5-ux04`) |

## CP-UX05 — consistência global

| Campo | Registro |
| --- | --- |
| Mudança | tela inicial na identidade nova; `grid-bg`/`glass` removidos; `TextField` compartilhado no lugar de 3 cópias |
| Testes | Chromium E2E 48 passed, 0 failed, 72 skipped (segunda execução completa); a primeira teve 1 falha em `API Real empty states…` que não reproduziu em 4 repetições isoladas nem em 12 paralelas (6 workers). Causa provável: compilação sob demanda do Vite de `sources.tsx` (2.300 linhas) logo após a edição, sob carga; registrada como intermitência observada, não como corrigida |
| Medidas | 400 telas (pt-BR e en-US): 0 nós axe, 0 estouro, 0 erro de console |
| Não é | tradução da interface das telas de produto (lacuna registrada na auditoria de UX); migração de todos os formulários para `Field` (sem necessidade comprovada pelo axe) |
| Commit | `af7a725` (push confirmado com `ls-remote`) |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS (CHANGELOG, auditoria, galeria `2026-11-v5-ux05`) |

## CP-UX06 — gate de experiência

| Campo | Registro |
| --- | --- |
| Navegadores | Chromium 49/0, Firefox 47/0, WebKit 47/0 (E2E com animação normal). No Firefox, com 6 workers, 3 testes estouraram tempo; passam em série e com 2 workers. Na auditoria da Assertiva (3 navegadores em paralelo, workers padrão), 4 testes no Firefox e 1 no WebKit falharam por carga: a suíte cruzada não é robusta sob paralelismo total |
| Desempenho | build de produção, `scripts/measure-vitals.mjs`: LCP ≤ 2,4 s com 4× CPU; CLS ≤ 0,073 depois de corrigir a tela inicial (0,14 → 0,002; a primeira correção piorou para 0,23 e foi refeita com uma face por peso); interação ≤ 80 ms, exceto Tracker 240 ms com 4× CPU (registrado) |
| Mutação de UI | `scripts/ui-mutants.py`: 6/10 → 9/10 mortos; o sobrevivente é equivalente. Achou 4 checagens que não podiam falhar (SH-NEW-036) |
| Assertiva (dogfood) | 1ª execução recusada pela própria trava de somente-leitura: o Vitest gravou `node_modules/.vite` no projeto através do link da cópia. Corrigido no repositório dono (`a91b445`, teste falha no código anterior). Depois: mutação real com StrykerJS em `retry.ts` e `search.ts`, 156 mutantes, 38 sobreviventes (escore ~76%); testes de limite acrescentados; nova medição: 156 mutantes, **13** sobreviventes (~92%), quase todos equivalentes (regex `\s` × `\s+` seguida de `filter(Boolean)`, fallbacks `?? ""`, status 3xx que nunca chega como erro); acionável: ordem de desempate do ranking, registrada. Um uso errado meu (`--mutate-tests` com Stryker) foi apontado pela ferramenta |
| Não é | leitor de tela (`NOT_RUN`: não há leitor disponível neste ambiente); auditoria de acessibilidade manual |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS |

## CP-CONTRACT01 — contrato cliente × API

| Campo | Registro |
| --- | --- |
| Pergunta | depois de SH-NEW-032, quantos outros corpos do cliente quebram o contrato (`extra="forbid"` nos 108 endpoints com corpo)? |
| Método | OpenAPI exportado para `apps/web/tests/contract/openapi.json` (deriva checada no pytest); teste Vitest usa o cliente em modo demo para produzir os objetos que as telas usam e envia as escritas pelo cliente real com `fetch` capturado, validando campos extras e obrigatórios recursivamente |
| Achado | SH-NEW-038: "Adicionar ao perfil" depois de importar texto respondia 422 na API real; confirmado com a API; corrigido com corpo só de campos do contrato |
| Cobertura | 10 escritas com objetos de domínio (Perfil, Lattes, Tracker, variantes, Mestre); escritas que montam literais na tela (~50) não foram verificadas uma a uma |
| Testes | Vitest 44/44 (controle negativo: o teste falha no código anterior; outro confere que pegaria SH-NEW-032); pytest 946 passed, 4 skipped; Chromium 49/0; API real 3/3 (inclui importar → adicionar) |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS |

## CP-DATA02 — round-trip de backup e restauração

| Campo | Registro |
| --- | --- |
| Pergunta | um backup feito pelo app devolve exatamente os dados de uma pessoa, e a restauração pode ser desfeita? |
| Método | `tests/test_data_round_trip.py`: preencher Perfil, Mestre, variante, Tracker e evidências pela API; backup; mudar todos os stores; restaurar; comparar pelo que a API responde; restaurar o backup de segurança (rollback) e comparar com o estado alterado |
| Achado | SH-NEW-039: o backup de segurança sobrescrevia o backup escolhido quando os dois caíam no mesmo segundo |
| Migrações | v6 (backfill), v6→v7 e v7→v8 cobertas por `test_storage_migrations.py` e executadas no pytest completo deste ciclo |
| Testes | os 2 testes novos falham no código anterior; dados: 8 passed |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS |

## CP-OPS01 — extensão no Chromium e custo do `ensure_database`

| Campo | Registro |
| --- | --- |
| C12 | ZIP do `scripts/package_extension.py` carregado com `--load-extension`: service worker MV3, popup sem erros, captura pelo fluxo do popup numa página do GitHub servida offline. Primeira versão do verificador assumia que `content.js` era injetado pelo manifesto (não é: o popup injeta sob demanda); corrigido no verificador, não na extensão. Controle negativo: ZIP sem `content.js` → `ok: false` |
| C26 | `ensure_database` medido: 12 ms por chamada (banco 1,7 MB). Cache por assinatura; duas tentativas erradas pegas pela medição (mtime do WAL muda a cada conexão; WAL vazio é apagado ao fechar). `list_nodes` 18 → 5,5 ms; pytest 103 s (antes 116 s) |
| Testes | pytest 952 passed, 4 skipped; 4 testes do cache (3 falham sem o cache) |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS |

## CP-SEC03 — DAST da API local

| Campo | Registro |
| --- | --- |
| Método | `scripts/dast_local_api.py` contra `scripts/run_api.py` em diretório sintético, sem credenciais: 14 sondas |
| Resultado | 14/14. Duas sondas estavam mal desenhadas e foram corrigidas, não mascaradas: um corpo de 6 MB "falhava" porque o servidor respondia 401 e fechava sem ler o corpo (correto); a expectativa de 413 antes do 401 vinha do Companion, e esta API autentica antes de olhar o tamanho (as duas ordens são seguras sem leitura do corpo) |
| Observação | rota inexistente sem sessão também responde 401: não há enumeração de rotas sem credencial |
| Revisão (CP-CI01) | o 14/14 superestimava duas sondas: a de corpo grande aceitava `ConnectionError` como recusa, e a de prova forjada parava no 403 da origem sem chegar à prova. Corrigidas no CP-CI01 |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS |

## CP-CI01 — CI remoto das quatro PRs e revisão de evidência

| Campo | Registro |
| --- | --- |
| SotuHire #57 em `63cda10` | CI falhou em três pontos: cópia do OpenAPI diferente (FastAPI/Pydantic mais novos no CI mudam títulos, `-Input`/`-Output` e `additionalProperties` sem mudar a API), `ruff format` em `apps/web/scripts/ui-mutants.py`, 2 erros de pyright em `scripts/verify_extension_in_chromium.py` |
| Correção do contrato | `scripts/export_openapi.py` grava uma visão do contrato (corpos de requisição, respostas 2xx, schemas alcançados; `additionalProperties` só onde a requisição alcança). Idêntica com FastAPI 0.138/Pydantic 2.13 e 0.163/2.14. Testes: campo novo na requisição e campo renomeado na resposta mudam a visão; título novo não |
| `ensure_database` (revisão pedida) | tamanho/mtime/tamanho do WAL não garantem identidade. Agora: hash do cabeçalho do banco (contador de mudanças, cookie do schema) e cabeçalho do WAL (sais mudam a cada reinício), validade de 10 min, invalidação no restore. 8 testes: reescrita do WAL sem crescimento (tamanho e mtime do banco iguais, comprovado no teste), 4 escritores concorrentes, restore, corrupção que preserva mtime (não vista dentro da janela, pega quando expira: limite documentado), arquivo corrompido substituído. 3 execuções seguidas verdes. Custo: chamada em cache 0,5 ms, verificação completa 19,6 ms |
| DAST (revisão pedida) | corpo grande por socket: 64 KB de 6 MB enviados, `HTTP/1.1 401` lido; silêncio é inconclusivo e falha. Prova forjada com origem permitida: 401 da prova. Travessia com sessão autorizada (pareamento real em diretório descartável): 5 caminhos 400/404, nenhum arquivo; controle positivo baixa o backup legítimo (`PK`); erros pós-autenticação sem caminho absoluto. 27/27; bootstrap errado → sai 1 |
| Assertiva #10 em `a91b445` | CI acusou `test_core_modules_do_not_name_tools[workspace.py]`: a correção de caches listava `.vite` no núcleo. `f1dec58`: adapters declaram `tool_cache_entries()`; `link_installed(..., local_only)`; teste de independência intocado. Local: 3.12 unit 1.161 + integração 193, 3.11 unit 1.161, `validate_repo` |
| Derivanta #12 | `db2dcc7` corrige os links (passo `check_markdown_links.py --strict-navigation` verde no CI). O job falha no passo seguinte, `check_documentation_structure.py`: 51 erros em 17 casos de eval; a `main` (`218761d`) falha no mesmo workflow desde 2026-10-28. Pré-existente, não corrigido nesta rodada; a PR não deve ser mesclada sem decisão do dono |
| Engine #4 | sem checks porque `.github/workflows` só dispara em `push` na `main` e `workflow_dispatch`; ausência de checks não é aprovação. Run manual 43774748903 na branch: 4 jobs de teste verdes (Ubuntu 3.12/3.13/3.14, Windows 3.12). `tools/verify.py` local num venv: lint, format, types, tests, conformance PASS. Workflow não alterado (decisão do dono) |
| CI em `ce31d94` | SotuHire #57: 11/11 checks verdes (Python 3.11/3.12 × Ubuntu/Windows, qualidade/cobertura/contratos, frontend unitário/build/E2E, extensão, regressão de IA, CodeQL Python e JS/TS). Assertiva #10 em `f1dec58`: CI verde (`validate`, Windows, Python 3.11; jobs condicionais pulados). Engine run 43774748903: todos os jobs verdes, inclusive mutation smoke e artefato empacotado. Derivanta #12: `Documentation integrity` vermelho na estrutura das evals (pré-existente). Instalação limpa a partir do arquivo de `ce31d94`: venv novo, lint, typecheck e build web |
| Reteste cruzado (P3) | `assertiva audit --execute --mutate modules/storage/migrations/runner.py` sobre os testes do cache e das migrações. A primeira tentativa rodou junto com um pytest completo no mesmo checkout e a guarda de somente-leitura abortou (exit 3): a suíte gravava `data/memory/career-profile.json` do checkout (SH-NEW-040, corrigido). Refeito numa worktree descartável: 226 mutantes, 104 mortos, 122 sobreviventes, a maioria na lógica de migração que estes dois arquivos não cobrem. No bloco do cache, os sobreviventes eram de dois tipos. Equivalentes ou inalcançáveis: anotações de tipo, tamanhos de prefixo 100/32, constante 600→601, guardas de corrida `FileNotFoundError` que o `is_file()` torna inalcançáveis. Lacunas reais: a aritmética e o limite da validade (`-`→`/`, `//`, `%`; `<`→`<=`), que o teste com validade 0 não distinguia, e `==`→`>=` na impressão digital. Dois testes novos (relógio controlado no limite exato; cópia mais antiga e menor posta no lugar) matam os quatro, conferido mutante a mutante |
| CI em `ac9e7d1` | 10/11: `Browser extension package` falhou. O job empacota a extensão num Python sem dependências e a varredura de segredos importa `modules.security`; o import de `modules.storage` (pydantic) no topo de `local_auth.py`, trazido pela correção do SH-NEW-040, quebrou esse import. Reproduzido num venv vazio (mesmo erro), corrigido com import tardio e coberto por teste que bloqueia pydantic/fastapi no import (falha no código anterior) |
| CI em `d3dc232` | 10/11: extensão verde; `Frontend unit, build and E2E` falhou no smoke do kanban (passou em `ce31d94` e `ac9e7d1`, sem mudança de frontend entre eles). O trace mostra outro card movido: `kanban-card.first()` não era o card criado. Causa provável: SH-NEW-041 (listagem em voo sobrescreve a criação). Teste endurecido (espera o quadro, arrasta o card criado pelo título): 10/10 em Chromium com 4 workers, Firefox e WebKit verdes; achado registrado como aberto |
| Matriz | rodapé dizia 8/19/1 com linhas 12 `DONE`/16 `PARTIAL`. Revisão de evidência: C03, C15, C18, C20 e UX-06 descem para `PARTIAL`. Agora C01–C28: 8 `DONE`, 20 `PARTIAL` |
| `CHANGELOG_GATE` / `DOCS_GATE` | PASS / PASS |

## Ferramentas (repositórios donos)

| Repo | Branch | SHA | Push | Testes |
| --- | --- | --- | --- | --- |
| Derivanta | `feat/approval-consumption-and-required-artifacts` | `db2dcc7` | confirmado | `scripts/tests` 26 passed; links verdes; estrutura de docs falha como na `main` (ver CP-CI01) |
| Derivanta-Engine | `feat/ci-workflow-checks` | `35f9951` | confirmado | `tools/verify.py` PASS; CI manual 43774748903 |
| Assertiva | `fix/precommit-hook-tool-identity` | `f1dec58` | confirmado | Python 3.12: unit 1.161, integração 193; 3.11: unit 1.161; `validate_repo` |