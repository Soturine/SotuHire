# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

## Unreleased

## [1.9.7] - 2026-07-14

### Adicionado

- Registry comum de 16 tarefas de IA, governança de prompts e defesa compartilhada contra prompt injection.
- AiRunStore 2.0 com latência, tokens, custo disponível, schema, contexto, evidência, fallback, retenção e paginação seguros.
- Golden datasets fictícios com 12 domínios, casos adversariais e métricas estruturais, de evidência, calibração, utilidade, operação e deduplicação.
- Benchmark reprodutível com mocks, local, providers opt-in, seed, resume, regressão e baselines sanitizados.
- Feedback humano, Outcome Learning não causal, APIs paginadas e painel `/ai-quality`.
- Migration 4 para feedback, benchmarks, resultados e eventos/métricas de outcome.

### Alterado

- Chamadas de IA passam a registrar provider/modelo solicitado e usado, prompt, fallback e métricas disponíveis sem persistir conteúdo pessoal integral.
- Gemini e OpenAI capturam uso/timing quando retornado e validam structured output; custo desconhecido permanece ausente.
- Extensão 0.9.3 adiciona feedback de análise GitHub vinculado somente a trace seguro.
- Catálogo de prompts inclui suíte, golden cases, benchmark, baseline e providers testados.

### Segurança

- Conteúdo importado é delimitado como não confiável, erros são sanitizados e segredos são excluídos de traces, benchmarks e feedback.
- Testes externos aceitam somente variáveis temporárias específicas e fixtures fictícias.

## [1.9.6] - 2026-07-12

### Adicionado

- Repository abstraction para JSON, JSONL e SQLite, com migrações locais versionadas.
- Migração dry-run/apply/verify com backup prévio, importação transacional, dedupe conservador e arquivos legados preservados.
- Backup, export, restore checksummed e data health, disponíveis também no painel de Privacidade.
- Snapshots imutáveis de vaga, currículo, análise e edital, ligados às candidaturas do Tracker.
- `AiRunStore` com provider/modelo/prompt/fallback/evidências sem armazenamento de segredos.
- Manifesto de capacidades, matriz de integração e catálogo de prompts gerados/verificados.
- Fundação de ingestão PDF/DOCX/HTML/TXT/JSON e interoperabilidade revisável com JSON Resume.
- Handshake de extensão/Companion/API, fila com retry/backoff/limite/export/import e prioridade para JSON-LD `JobPosting`.
- Testes de repositories, migração, snapshots, restore, health, extensão e integração de dados.

### Alterado

- Tracker passa a preservar stage history e vínculos com vaga, currículo e análises usados.
- Identidade de Perfil, memória, vaga, edital e GitHub preserva referências sem colapsar fatos distintos do mesmo container.
- Career Context mantém confiança, confirmação, sensibilidade e `source_ref`; ATS/Tailor/Radar não promovem item não confirmado a fato seguro.
- Permissões de IA de Perfil, Lattes, Extensão e Notificações passam a ser aplicadas pelo runtime.
- Frontend preserva warnings, request ID, trace, candidatos GitHub e contexto do Tracker.
- README, roadmap, índices, arquitetura de dados e documentação da extensão foram reorganizados como referências atuais.
- Versões do app, API e frontend alinhadas; extensão atualizada de forma independente por conter mudanças funcionais.

### Corrigido

- Fallback OpenAI no GitHub não é mais marcado como fallback Gemini.
- Health check de SQLite é realmente read-only, inclusive em banco pré-schema ou corrompido.
- Restore valida formato, versão, checksum, schema, integridade e foreign keys do SQLite antes de gravar.
- Manifesto de backup registra schema real e versão máxima suportada.
- Timelines legadas de edital são normalizadas para o contrato de snapshot.
- FKs de snapshots usam restrição de exclusão coerente com imutabilidade.
- Scripts de dados funcionam quando executados diretamente fora da raiz do repositório.

### Segurança

- Chaves expostas não foram usadas; testes externos continuam opt-in e skipped sem chave temporária nova.
- Backup/export excluem secrets por caminho, nome e padrões de conteúdo; pacote da extensão amplia o secret scan.
- Sem auto-apply, inscrição, pagamento, envio de documentos ou scraping autenticado novo.
- Sem alteração no fluxo `authenticated-browser`.

## [1.9.5] - 2026-07-11

### Adicionado

- Identidade e deduplicação compartilhadas para Perfil, memória, oportunidades, projetos e editais.
- Trace de IA com provider/modelo solicitado e usado, prompt/versionamento, fallback e evidências.
- Sete personas multiárea coerentes e restauração segura da demo.
- Dashboard agregado, verificação de checkout limpo, roteiro e case study.
- Captura padronizada de screenshots/GIF do produto e extensão.

### Alterado

- Extensão atualizada para v0.9.1 com UI moderna, fila offline, análise independente local e providers Gemini/OpenAI próprios opcionais.
- Catálogos Gemini/OpenAI consultados nas APIs oficiais, com cache e seleção de modelo aplicada à chamada real.
- Enriquecimento público de perfis/repositórios GitHub com README, commits, estrutura, linguagens e atividade, sem autenticação.
- `source_ref` percorre Perfil -> Career Context -> APIs/UI.
- `pyproject.toml` passa a sustentar o comando documentado `pip install -e .[dev]`.
- Build PEP 517, verificador imune a `PIP_NO_BUILD_ISOLATION` externo e EOL LF portável.
- Settings remove implementação antiga não consumida; mocks e versões foram alinhados.

### Segurança

- Chaves próprias da extensão isoladas no service worker, em sessão por padrão e persistidas somente com consentimento; nunca em `chrome.sync` ou content script.
- Chave configurada no app continua exclusivamente no backend local e nunca é devolvida à extensão.
- Sem auto-apply, inscrição, pagamento, envio de documentos ou scraping autenticado novo.
- Sem alteração no `authenticated-browser`.

## [1.9.4] - 2026-07-07

### Adicionado

- Presets de IA em Configurações: Local seguro, IA básica, IA completa e Personalizado.
- Catálogo de modelos por provider com endpoints `/api/v1/settings/ai/providers`, `/models` e `/models/refresh`.
- Provider OpenAI no backend local, com secret separado, modelo selecionado, teste de conexão mockável e fallback local.
- Cache local de catálogo em `data/settings/ai-models-cache.json` e segredos locais ignorados por Git em `data/secrets/`.
- Testes opt-in `external_ai` para Gemini/OpenAI reais via `SOTUHIRE_TEST_GEMINI_API_KEY` e `SOTUHIRE_TEST_OPENAI_API_KEY`.
- Extensão com ação **Capturar edital / concurso**, tipo `public_exam`, endpoint local `/capture/public-exam` e contexto seguro `/capture/context-summary`.
- Importação de captura da extensão para `/public-exams?capture_id=...` como rascunho revisável.
- Documentação de catálogo de modelos, QA ponta a ponta e ponte segura da extensão.

### Alterado

- Gemini e OpenAI usam o modelo salvo no backend local nos fluxos estruturados.
- `openai_future` é normalizado para `openai` para compatibilidade com configurações antigas.
- Settings de IA deixam de exibir uma lista gigante por padrão e agrupam opções avançadas.
- Editais/Concursos retornam `requested_provider`, `provider_used` e `analysis_mode` com fallback local quando provider falha.
- Área de Fontes/Captura diferencia `public_exam` de vaga privada e permite importar como edital.
- A extensão consulta apenas resumo seguro do Perfil Universal; não recebe perfil inteiro, memória completa ou chave de IA.
- README, docs, MkDocs e roadmap atualizados para v1.9.4.

### Segurança

- API keys continuam restritas ao backend local/env local.
- Sem API key no frontend, `localStorage`, `sessionStorage`, extensão, docs, fixtures ou release notes.
- Sem inscrição automática, candidatura automática, pagamento, boleto ou envio automático de documentos.
- Sem login em banca/órgão, crawler logado, captura de cookies/tokens/sessão/headers ou bypass de CAPTCHA.
- Sem alteração no fluxo `/api/v1/sources/authenticated-browser/collect`.

## [1.9.3] - 2026-07-03

### Adicionado

- `modules/public_exams` com modelos, parser local, service, scoring, store, formatadores e plano de estudo inicial.
- Importação de edital por texto colado com extração local de órgão, banca, cargo, salário, taxa, datas, requisitos, etapas, documentos e conteúdo programático.
- Endpoints `/api/v1/public-exams` para importar draft, listar, consultar, confirmar, excluir, analisar e gerar plano de estudo.
- Prompt `public_exam_notice_extractor_v1` para estruturar editais com Gemini opcional como rascunho revisável.
- Tela `/public-exams` no frontend web com análise, warnings, cargos, timeline, requisitos, checklist, Exam Fit Score e plano inicial.
- Comparação inicial com o Perfil Profissional Universal, Career Context Engine `public_exams` e evidências acadêmicas/Lattes já confirmadas.
- Preparação de Radar/Tracker para tipos e status de oportunidades públicas sem misturar com candidatura privada.

### Alterado

- Health API anuncia `public_exams_foundation`.
- Radar passa a reconhecer `public_exam`, `academic_call`, `scholarship`, `residency` e `internship_public` como tipos separados.
- README, roadmap, mapa de integração, docs de concursos/editais, Prompt Registry e MkDocs documentam a fundação v1.9.3.
- Versão do projeto, API e frontend atualizada para `1.9.3`.

### Segurança

- Sem inscrição automática em concurso, edital, bolsa, residência, estágio público ou chamada pública.
- Sem pagamento automático, boleto automático ou envio automático de documentos.
- Sem login em banca/órgão, scraping autenticado, crawler logado ou bypass de CAPTCHA.
- Sem API key do app no frontend.
- IA não salva edital nem decide elegibilidade final sem revisão humana.
- O edital oficial sempre prevalece.
- Sem alteração no fluxo `/api/v1/sources/authenticated-browser/collect`.

## [1.9.2] - 2026-06-30

### Adicionado

- `modules/academic` com parser local de texto colado do Currículo Lattes.
- Endpoints `/api/v1/profile/import-lattes`, `/api/v1/profile/lattes/draft` e `/api/v1/profile/lattes/confirm`.
- Prompt `profile_lattes_extractor_v1` para extração acadêmica assistida por Gemini.
- Seção **Acadêmico / Lattes** na rota `/profile`.
- Evidências acadêmicas no Career Context Engine com purposes `academic`, `lattes` e `public_exams`.
- Fundação documental para editais e concursos.

### Alterado

- README e docs principais revisados com português, acentos e linguagem mais consistente.
- ATS, Tailor e GitHub/Portfólio passam a considerar evidências acadêmicas confirmadas no Perfil Profissional Universal.
- Roadmap, MkDocs, índice documental e catálogo de prompts documentam Lattes/acadêmico.
- Versão do projeto, API e frontend atualizada para `1.9.2`.

### Segurança

- Nada extraído do Lattes é salvo sem revisão humana.
- Gemini atua como extrator assistido, não como fonte de verdade.
- Sem login, scraping autenticado ou crawler do Lattes.
- Sem inscrição automática em concursos ou editais.
- Sem alteração no fluxo `/api/v1/sources/authenticated-browser/*`.

## [1.9.1] - 2026-06-30

### Adicionado

- `modules/context` com Career Context Engine para Perfil Universal, RAG local e sinais do produto.
- Formatadores de contexto para prompts locais/externos, evidências do Match Engine e candidatos de perfil vindos de GitHub/Portfólio.
- Integração inicial de contexto em Wishlist, Radar, Scheduler, Match, ATS, Tailor, Tracker, Fontes, Notificações e GitHub/Portfolio.
- Testes para engine, deduplicação, RAG local, privacidade, APIs de contexto e README.
- Script `scripts/capture_web_walkthrough.py` para screenshots/GIF do frontend web moderno.
- Documentação do Career Context Engine e release notes v1.9.1.

### Alterado

- README reestruturado como página profissional do projeto, sem seções internas presas a versões antigas.
- Screenshots e GIF principais agora usam nomes sem versão.
- `MemoryStore()` passa a respeitar `SOTUHIRE_DATA_DIR` por padrão.
- Roadmap, mapa de integração, índice documental e MkDocs atualizados para refletir contexto unificado.
- Versão do projeto, API e frontend atualizada para `1.9.1`.

### Corrigido

- Tag `v1.9.0` revisada no commit final da main com `package-lock.json` validado.
- Validação do lockfile do frontend confirmada com `npm ci`.

### Segurança

- Contexto sensível é omitido de payload externo.
- Dados de perfil/memória só vão para provider externo quando `allow_memory_context=true`.
- GitHub/Portfólio retorna candidatos de evidência para revisão, sem salvar automaticamente no Perfil.
- Nenhum fluxo de authenticated browser, Chromium/CDP, cookie, token, sessão, headers, CAPTCHA ou auto-apply foi alterado.

## [1.9.0] - 2026-06-29

### Adicionado

- Scheduler local do Radar com CRUD em `/api/v1/radar/schedules`.
- Execução manual `run now` por agendamento.
- Histórico local de runs agendadas em `/api/v1/radar/scheduled-runs`.
- Runtime local com `/api/v1/radar/scheduler/status`, `start` e `stop`.
- Quiet hours e cooldown contra notificações repetidas.
- Central local de notificações em `/api/v1/notifications`.
- Seção **Agendamentos** e painel de notificações na tela Radar.
- Uso opcional do Perfil Profissional Universal em agendamentos.
- Testes backend e E2E para agendamentos, notificações e regressão de storage.

### Alterado

- Health API anuncia capabilities de `scheduled_radar` e `local_notifications`.
- Radar passa a aceitar fonte `authenticated_assisted_capture` como lembrete agendável e revisável.
- README, roadmap e docs de desenvolvimento documentam v1.9.0.
- Versão do projeto, API e frontend atualizada para `1.9.0`.

### Segurança

- Agendamentos não fazem auto-apply, envio automático de currículo ou candidatura.
- Captura assistida autenticada agendada não coleta cookie, token, sessão, headers ou storage de terceiros.
- API key continua backend-side e nunca retorna ao frontend.

## [1.8.2] - 2026-06-29

### Adicionado

- Perfil Profissional Universal persistido localmente em `data/profile/profiles.json`.
- Nova tela `/profile` no frontend moderno.
- Endpoints `/api/v1/profile*` para consultar, editar, importar texto, deduplicar e montar contexto.
- Prompt `profile_items_extractor_v1` no Prompt Registry.
- Extração local multiárea para itens de perfil com revisão humana obrigatória.
- Filtro por tipo e edição inline de itens do perfil no frontend.
- Integração do perfil persistido com Wishlist/Radar quando `use_profile_context=true`.
- Integração inicial segura de `ProfileContext` em Match/Tailor e captura de fontes.
- Endpoint `POST /api/v1/sources/authenticated-captures` para captura assistida autenticada revisável.
- Testes backend e frontend para perfil, importação, fallback, dedupe, multiárea e captura assistida.

### Alterado

- `ProfileContextOrchestrator` agora usa o Perfil Profissional Universal persistido antes do store legado.
- Health API anuncia capabilities de Perfil Profissional Universal e captura assistida autenticada.
- README, roadmap, mapa de integração, catálogo de prompts, docs frontend e release notes documentam v1.8.2.
- Versão do projeto, API e frontend atualizada para `1.8.2`.

### Segurança

- Itens extraídos por IA nunca são confirmados automaticamente.
- API key continua backend-side e nunca retorna ao frontend.
- Dados do perfil só entram em provider externo quando `allow_memory_context=true`.
- Captura assistida rejeita metadata com cookie, token, sessão, headers ou segredos.
- Nenhum fluxo sensível de authenticated browser, Chromium/CDP, crawler logado, CAPTCHA ou auto-apply foi alterado.

## [1.8.1] - 2026-06-29

### Adicionado

- Endpoint `POST /api/v1/radar/wishlists/draft` para gerar rascunho de wishlist a partir de texto livre.
- Prompt `job_wishlist_builder_v1` no Prompt Registry.
- Fallback local multiárea para wishlist do Radar, sem assumir tecnologia, GitHub, CLT, diploma ou experiência formal.
- `ProfileContext` e `ProfileContextOrchestrator` como preparação para Perfil Profissional Universal.
- Seção **Criar wishlist com IA** na tela Radar.
- Toggles de IA para currículo, vaga, importações e Radar.
- CI com frontend `npm ci`, lint, typecheck, build, smoke E2E Chromium e empacotamento da extensão.

### Alterado

- Radar mostra erros de fonte no card e desabilita execução quando não há fonte ativa.
- Wishlist do Radar ganhou campos editáveis para domínio, senioridade, termos a evitar, ATS mínimo e notas.
- README, roadmap, mapa de integração, docs de Radar e Prompt Registry atualizados para v1.8.1.
- Versão do projeto, API e frontend atualizada para `1.8.1`.

### Segurança

- Wishlist gerada por IA/local nunca é salva automaticamente.
- API key continua backend-side e nunca retorna ao frontend.
- Scores finais continuam no backend/core.
- Nenhum fluxo sensível de authenticated browser, Chromium/CDP, crawler logado, cookie, token, sessão,
  CAPTCHA ou auto-apply foi alterado.

### Validação

- Testes backend cobrem draft local, exemplos multiárea, Gemini fake, fallback por JSON inválido,
  toggle `allow_radar=false`, ausência de segredo e não persistência automática.
- Playwright cobre geração de draft, preenchimento do formulário, edição antes de salvar e regressões
  de storage/branding existentes.

## [1.8.0] - 2026-06-27

### Adicionado

- Tela **Radar de Vagas** no frontend moderno.
- Modelos e store local para `JobWishlist`, `RadarSource`, `RadarRun`, `RadarResult` e `RadarAlert`.
- Endpoints `/api/v1/radar/*` para wishlists, fontes, rodadas, resultados, alertas e estatísticas.
- Suporte a RSS/Atom público com refresh manual e revisão antes de salvar.
- Estrutura de adapters para APIs oficiais documentadas.
- Alertas locais para oportunidades acima do score mínimo da wishlist.
- Ações para salvar resultados do Radar na Caixa de Entrada ou em Candidaturas.
- Prompt `job_radar_match_explanation_v1` para explicação opcional com IA.
- Testes backend e E2E para Radar, alertas, RSS fake e modo Demo/API Real.

### Alterado

- Diretório de Fontes marca RSS público como disponível via Radar manual.
- README, roadmap, mapa de integração e docs de fontes documentam Radar, feeds públicos e limites.
- Health API anuncia capability `job_radar`.

### Segurança

- Score final do Radar permanece no backend/core.
- IA opcional apenas explica evidências/lacunas e faz fallback local.
- Nenhuma API key é salva ou retornada pelo frontend.
- Nenhum fluxo sensível de authenticated browser, Chromium/CDP, login manual, cookie, token,
  CAPTCHA, crawler logado ou auto-apply foi alterado.

## [1.7.1] - 2026-06-26

### Corrigido

- Textos públicos com mojibake no Kanban e teste de regressão para sequências comuns de encoding.
- Separação visual entre Modo Demo e API Real na Caixa de Entrada.
- Empty state da API Real sem oportunidades, sem misturar dados fictícios silenciosamente.
- Textos do Kanban para estágio, filtro, rejeição, análise e criação de candidatura.

### Adicionado

- Upload real de CSV/JSON pelo navegador com preview e confirmação antes de importar.
- Fluxo visual de mescla de duplicatas preservando histórico, fonte, link e notas.
- Exportação da Caixa de Entrada em CSV e JSON.
- Diretório de Fontes em **Fontes e Captura** para fontes públicas, feeds, APIs oficiais, CSV/JSON
  recorrente e links manuais.
- Endpoint `POST /api/v1/sources/captures/{capture_id}/merge`.
- Endpoints `GET /api/v1/sources/directory` e `POST /api/v1/sources/export`.
- Prompt `source_import_enrichment_v1` e schema seguro para enriquecimento opcional de importações.

### Alterado

- Importadores aceitam `use_ai=true` e fazem fallback local se provider não estiver configurado ou
  falhar.
- Duplicatas exibem comparação entre item novo e item existente.
- Fontes públicas/feeds ficam preparadas como diretório seguro, sem crawler amplo ou automação de
  conta.
- Roadmap, docs de fontes e mapa de integração atualizados para v1.7.1.

### Segurança

- Nenhuma chave de IA é salva no frontend, no `localStorage` ou no `sessionStorage`.
- A API key nunca retorna ao frontend e não entra em mocks, docs, prints ou testes.
- Nenhum fluxo de authenticated browser, Chromium/CDP, login manual, CAPTCHA, cookie, token,
  crawler logado ou auto-apply foi alterado.

### Validação

- Testes backend direcionados cobrem upload lógico CSV/JSON, merge, export, diretório, fallback de IA
  e ausência de segredo.
- Playwright cobre upload CSV/JSON via browser, preview antes da importação, merge visual, export,
  diretório de fontes, empty state API Real e regressão contra mojibake público.

## [1.7.0] - 2026-06-26

### Adicionado

- Caixa de Entrada de Oportunidades em **Fontes e Captura**.
- Importadores locais por texto, link, CSV e JSON.
- Histórico persistente de capturas/importações em store local ignorado pelo Git.
- Modelos `JobSource`, `JobImport`, `CaptureRecord`, `OpportunityInboxItem`, `ImportBatch` e
  `DuplicateCandidate`.
- Endpoints `/api/v1/sources/imports*`, `/api/v1/sources/captures*`, `/api/v1/sources/dedupe` e
  `/api/v1/sources/stats`.
- Deduplicação local explicavel por URL normalizada, empresa+cargo+localidade e texto normalizado.
- Ações para importar oportunidade para Vaga, salvar em Candidaturas e preservar origem no tracker.
- Histórico da extensão/local companion com patch seguro de status local.
- Screenshots e GIF v1.7 padronizados para os fluxos de importação.
- Documento `docs/07-development/v1.7.0-public-sources-importers-capture-history.md`.

### Alterado

- Fontes e Captura virou fluxo pratico de intake: texto/link/CSV/JSON, filtros, busca, duplicatas e
  fontes públicas planejadas.
- Cards do tracker preservam contexto de origem ao salvar itens importados.
- README, docs de frontend, mapa de integração, visual preview e guia da extensão foram atualizados
  para v1.7.0.

### Segurança

- O importador de URL faz apenas leitura pública simples e orienta colar texto quando a página
  bloqueia acesso, exige login ou não traz conteúdo legível.
- Nenhum fluxo sensível de authenticated browser, Chromium/CDP, login manual, crawler logado,
  CAPTCHA ou auto-apply foi alterado.
- Nenhum dado real, API key ou segredo foi usado em mocks, testes, docs ou screenshots.

### Validação

- Testes backend cobrem importação texto/link/CSV/JSON, dedupe, stats, captura para Vaga e tracker.
- Playwright cobre Caixa de Entrada, importações fake, duplicata, Kanban com origem e ausencia de
  branding legado público.

## [1.6.0] - 2026-06-24

### Adicionado

- Cobertura E2E cross-browser para Chromium, Firefox e WebKit.
- QA responsivo para mobile `390x844`, tablet `768x1024` e desktop `1440x1000`.
- Kanban com drag-and-drop visual, atualização otimista e rollback quando a API falha.
- Histórico mais rico da Extensão Local em Fontes e Captura.
- Estados de IA/fallback mais claros para provider local, configurado, não configurado, timeout,
  limite/erro e chave invalida.
- Screenshots v1.6 e GIF walkthrough v1.6 com dimensões padronizadas.
- Documento `docs/07-development/v1.6.0-stability-cross-browser-kanban.md`.

### Alterado

- Status do Kanban no frontend alinhados aos enums reais do backend.
- Match, ATS, Tailor e GitHub agora mostram explicabilidade, evidências usadas e prioridade de
  melhoria.
- Launcher Windows detecta portas ocupadas e mostra processo/PID.
- README raiz, docs de frontend, scripts e visual preview atualizados para v1.6.0.

### Segurança

- A chave de IA continua backend-side e nunca retorna ao frontend.
- Nenhum fluxo de authenticated browser, Chromium/CDP, scraper autenticado, crawler logado ou
  auto-apply foi alterado.
- Screenshots e mocks usam apenas dados fictícios.

### Validação

- Playwright executado em Chromium, Firefox e WebKit.
- Testes backend cobrem metadados seguros da ponte da extensão.
- Responsividade validada sem overflow horizontal de página nas rotas principais.

## [1.5.1] - 2026-06-23

### Adicionado

- Auditoria de prontidão de produto v1.5.1 com status real por funcionalidade.
- Fluxo guiado web-first na Home e no Dashboard.
- Blocos de recomendações acionáveis em Compatibilidade, ATS, Ajuste de Currículo e GitHub.
- E2E expandido para demos, IA Settings, Fontes e Captura, Kanban e branding legado.
- Screenshots v1.5.1 padronizados em `1440x1000` por Playwright.
- GIF walkthrough v1.5.1 mais lento e legível.

### Alterado

- Badges e textos de Local/IA/Fallback padronizados nas telas de análise.
- Painel **Extensão Local** mostra status do companion, origem, data, tipo e ações por captura.
- Kanban mostra origem, score, última análise, notas e data nos cards/lista.
- README raiz, `apps/web/README.md`, `scripts/README.md`, visual preview e mapa de integração
  atualizados para v1.5.1.
- Versão do projeto, API e frontend atualizada para `1.5.1`.

### Segurança

- A chave de IA continua backend-side e nunca retorna ao frontend.
- Nenhum fluxo de authenticated browser, Chromium/CDP, scraper autenticado, crawler logado ou
  auto-apply foi alterado.
- Screenshots e mocks usam apenas dados fictícios.

### Validação

- Testes backend adicionais cobrem toggles de IA por área e importações fake da extensão.
- Playwright cobre fluxo guiado, demos, IA Settings, Sources, Kanban e capturas visuais.

## [1.5.0] - 2026-06-23

### Adicionado

- Roteamento backend-side de IA opcional por área para currículo, vaga, compatibilidade, ATS,
  Tailor e GitHub.
- Prompts `match_analysis_evidence_based_v1`, `ats_analysis_v1`, `resume_tailor_v1` e
  `career_advice_v1` no Prompt Registry programático.
- Badges de provider/fallback no frontend moderno.
- Ponte FastAPI `/api/v1/extension/*` para capturas locais da Local Companion API.
- Painel **Extensão Local** em **Fontes e Captura**.
- Flag `-WithCompanion` no launcher web-first.
- Auditoria de integração v1.5 e mapa de integração de módulos.
- Testes de roteamento de IA, fallback local e ponte da extensão.

### Alterado

- Launcher Windows consolidado em `scripts/windows/start-sotuhire.ps1`.
- Wrappers `scripts/windows/start-api.ps1` e `scripts/windows/start-web.ps1` removidos por serem
  apenas delegadores.
- Frontend mostra quando uma análise usou local, Gemini ou fallback local.
- Local Companion capture store respeita `SOTUHIRE_DATA_DIR` para testes isolados.
- Versão do projeto, API e frontend atualizada para `1.5.0`.

### Segurança

- A chave de IA continua armazenada apenas no backend local e nunca retorna ao frontend.
- Gemini falha com fallback local e warning, sem quebrar análises.
- Scores finais continuam no backend/core.
- Nenhum fluxo de authenticated browser, Chromium/CDP, scraper autenticado, crawler logado ou
  auto-apply foi alterado.

### Validação

- Testes backend adicionados para rota Gemini fake, fallback e bridge da extensão.
- Smoke/E2E frontend cobre o painel **Extensão Local**.

## [1.4.0] - 2026-06-22

### Adicionado

- Launcher web-first para Windows com `.\start-sotuhire.ps1`.
- Scripts `scripts/windows/start-sotuhire.ps1`, `start-api.ps1` e `start-web.ps1`.
- Documentação de scripts em `scripts/README.md`.
- Endpoints seguros de IA em `/api/v1/settings/ai`.
- Armazenamento backend-side local para metadados e segredo de provider.
- Integração real da tela **Configurações → IA e Providers** com a FastAPI local.
- Smoke/E2E com Playwright em `apps/web`.
- Documento `docs/07-development/v1.4.0-web-first-local-launcher.md`.

### Alterado

- Frontend moderno em `apps/web` documentado como experiência local principal.
- Streamlit documentado como modo legado/dev/local debug, sem remoção de `app.py`.
- Versão do projeto, API e frontend atualizada para `1.4.0`.
- README raiz, docs de frontend e arquitetura atualizados para o fluxo web-first.

### Segurança

- A chave de IA fica apenas no backend local, em `data/secrets/ai-provider.local.json`.
- A API nunca retorna a chave para o frontend.
- O frontend não salva chave em `localStorage` ou `sessionStorage`.
- `data/`, `.env.local`, `apps/web/.env.local` e logs locais do launcher são ignorados pelo Git.
- Nenhum fluxo de authenticated browser, Chromium/CDP, scraper autenticado, crawler logado ou
  auto-apply foi alterado.

### Validação

- Testes de API dedicados para `settings/ai`.
- OpenAPI validado para `/api/v1/settings/ai`, `/api/v1/settings/ai/status` e
  `/api/v1/settings/ai/test`.
- Frontend: `npm run build`, `npm run lint`, `npm run typecheck` e `npm run test:e2e`.

## [1.3.0] - 2026-06-22

### Adicionado

- Frontend moderno em `apps/web`, integrado diretamente no repositório sem substituir a raiz.
- Stack React, Vite, TypeScript, TanStack Router, TanStack Query, Tailwind CSS, Radix UI,
  Recharts e lucide-react.
- Modo Demo com dados fictícios e modo API Real consumindo `http://127.0.0.1:8787/api/v1`.
- Client HTTP preparado para o envelope `{ ok, data, warnings, request_id }` da FastAPI local.
- Telas de Home/Landing, Dashboard, Currículo, Vaga, Análise de Compatibilidade, Análise ATS,
  Ajuste de Currículo, Análise de GitHub, Candidaturas, Inteligência de Candidaturas, Fontes e
  Captura, Configurações e Privacidade.
- Página **Fontes e Captura** integrada ao menu e à rota `/sources`.
- UI de **IA e Providers** em Configurações, marcada como integração planejada com backend local.
- Screenshots v1.3 do frontend moderno e walkthrough GIF em `docs/assets/screenshots`.
- Documento de desenvolvimento `docs/07-development/v1.3.0-modern-web-frontend.md`.

### Alterado

- Versão do projeto e da API local atualizada para `1.3.0`.
- README raiz atualizado com preview do frontend moderno, comandos `apps/web`, modo Demo/API Real
  e limites de segurança.
- Docs de frontend atualizados para refletir que o app moderno existe em `apps/web`.
- Visual preview atualizado para screenshots v1.3.
- Linguagem pública do produto alinhada para Análise de Compatibilidade, Pontuação de
  compatibilidade, Aderência, Confiança e Risco.

### Segurança

- Nenhum segredo é colocado no frontend.
- API keys não são persistidas em `localStorage` ou `sessionStorage`.
- Scores reais continuam no backend/core; o frontend não move regra de negócio crítica.
- O navegador autenticado autorizado existente foi exposto no frontend; ele exige login manual,
  autorização explícita, não contorna CAPTCHA/checkpoint e não faz auto apply.
- Streamlit, FastAPI, docs e testes existentes permanecem preservados.

### Validação

- Frontend: `npm install`, `npm run build`, `npm run lint` e `npm run typecheck`.
- OpenAPI validado para `/api/v1/health`, `/api/v1/match/analyze`, `/api/v1/ats/analyze` e
  `/api/v1/resume/tailor`.
- Smoke visual com Playwright/Chrome local cobrindo as rotas principais e ações demo.

## [1.2.0] - 2026-06-22

### Adicionado

- FastAPI local em `apps/api`, com `create_app()`, OpenAPI e docs interativas.
- Endpoint `GET /api/v1/health`.
- Endpoints de analise `POST /api/v1/resume/extract`, `POST /api/v1/job/extract`,
  `POST /api/v1/match/analyze`, `POST /api/v1/ats/analyze`, `POST /api/v1/resume/tailor` e
  `POST /api/v1/github/repo/analyze`.
- Endpoints do tracker `GET/POST /api/v1/tracker/jobs` e
  `PATCH /api/v1/tracker/jobs/{id}`.
- Endpoints de Application Intelligence `GET /api/v1/tracker/metrics`,
  `GET /api/v1/tracker/requirements`, `GET /api/v1/tracker/funnel` e
  `GET /api/v1/tracker/sources`.
- DTOs Pydantic para requests/responses da API, com envelope `ok`, `data`, `warnings` e
  `request_id`.
- Configuração local por env: `SOTUHIRE_API_HOST`, `SOTUHIRE_API_PORT` e
  `SOTUHIRE_API_ALLOWED_ORIGINS`.
- Script `scripts/run_api.py` para subir a API local.
- Funcoes de Application Intelligence em `modules/tracker/dashboard.py`, incluindo ranking por
  status, ranking por source, missing requirements, critical gaps, funnel e source metrics.
- Testes dedicados para health, resume, job, match, ATS, Tailor, GitHub, tracker e Application
  Intelligence.

### Alterado

- Versão do projeto atualizada para `1.2.0`.
- `docs/08-frontend/api-contract.md` passou a documentar a API real implementada na v1.2.0.
- Documentação de arquitetura passou a diferenciar Frontend API Layer e Local Companion API.
- README raiz passou a documentar `python scripts/run_api.py`, OpenAPI e `/api/v1`.
- Dependências FastAPI/Uvicorn/HTTPX foram adicionadas em `docs/requirements/requirements.txt`.

### Segurança

- CORS e restrito por default, sem wildcard.
- Respostas de resume/job extraction removem `raw_text` por default.
- A API reutiliza regras do core e não move Match, ATS, Tailor, GitHub Analyzer ou métricas oficiais
  para o frontend.
- Tracker continua local-first e sem armazenar currículo bruto.
- GitHub Analyzer aceita `fallback_payload` com dados públicos/capturados sem expor tokens no
  frontend.

### Validação

- Precheck antes da implementação: `ruff check .`, `ruff format --check .`, `pytest`,
  `mkdocs build --strict`, `python -m compileall modules tests`, `pyright` e
  `node --check docs/javascripts/sotuhire-demo.js`.
- Testes focados da API e Application Intelligence: `13 passed`.

## [1.1.0] - 2026-06-22

### Adicionado

- Documentação frontend-ready em `docs/08-frontend`, incluindo arquitetura, handoff Lovable,
  screen map, API contract, mock data contract, design notes, frontend rules e Application
  Intelligence.
- Mocks JSON oficiais em `docs/assets/mock-api` para prototipação de frontend.
- Home pública dedicada em `docs/index.md` para o GitHub Pages.
- Demo estática v1.1 em `docs/08-frontend/static-demo.md`.
- Estrutura reservada `apps/web` para um frontend moderno futuro.

### Alterado

- Versão do projeto atualizada para `1.1.0`.
- `docs/README.md` passou a ser índice documental do repositório, enquanto `docs/index.md` virou a
  home do site.
- Roadmap atualizado com v1.1.0, v1.2.0, v1.3.0, v1.4.0 e v2.0.0.
- README raiz passou a explicar Streamlit como app local atual/dev, GitHub Pages como site estático
  e Lovable/React como frontend futuro guiado por contratos.

### Segurança

- Documentado que o frontend futuro não deve conter API keys, Gemini key, GitHub token ou regras
  críticas de negócio.
- Reforçado que GitHub Pages continua estático e não roda backend.
- Mocks usam apenas dados fictícios.

### Validação

- QA final planejado com `ruff check .`, `ruff format --check .`, `pytest`, `mkdocs build --strict`,
  `python -m compileall modules tests`, `pyright` e `node --check docs/javascripts/sotuhire-demo.js`.

## [1.0.0] - 2026-06-21

### Adicionado

- Apresentação do Match Engine 2.0 no fluxo principal, com `Confidence`, `Evidence Score`, gaps
  críticos, requisitos atendidos/parciais/ausentes, competências transferíveis, evidências usadas e
  ações seguras.
- Enriquecimento determinístico do `analyze_structured` com Match Engine 2.0, mantendo fallback
  legado quando a extração estruturada local não estiver disponível.
- Classificação ATS baseada em evidências do Match Engine 2.0, separando keywords presentes,
  keywords que só devem ser adicionadas se forem verdadeiras e keywords sem evidência.
- Resume Tailor usando evidências do Match Engine 2.0 para keywords seguras, warnings e gaps
  críticos.
- Pesos configuráveis por domínio em `modules/matching/domain_weights.py`, com perfis iniciais para
  enfermagem/saúde, arquitetura, cybersecurity, pedagogia e engenharia civil.
- Demos fictícias multiárea em `examples/` e outputs estáticos em `examples/outputs/`.
- GitHub Pages preparado como site estático de produto, documentação e demo, com páginas sobre
  demo v1.0 e diferença entre Pages e app local.
- Documento de desenvolvimento `docs/07-development/v1.0.0-stable-release.md`.

### Alterado

- Versão do projeto atualizada para `1.0.0`.
- README, roadmap, visão, regras de matching e docs do Match Engine foram atualizados para refletir
  a versão estável v1.0.0.
- A home do MkDocs passou a apresentar o produto como site público estático, sem prometer execução
  do backend no GitHub Pages.
- A UI diferencia melhor score, confidence, evidência e risco.

### Segurança

- O GitHub Pages é documentado explicitamente como site estático; o app completo continua local via
  Streamlit/Local Companion API.
- Demos usam apenas nomes, empresas e cenários fictícios.
- Tailor e ATS preservam linguagem condicional para itens sem evidência.
- Nenhum comportamento de coleta autenticada, compliance ou exposição de API keys foi alterado.

### Validação

- QA final executado com `ruff check .`, `ruff format --check .`, `pytest`, `mkdocs build --strict`,
  `python -m compileall modules tests` e `pyright`.

## [0.12.0] - 2026-06-21

### Adicionado

- Módulo `modules/matching` com models Pydantic, exceptions, requirement matcher, evidence matcher,
  transferable skills, score calculator, risk adjustment, confidence scoring, explanation builder e
  engine determinística.
- Catálogo inicial de registros e conselhos profissionais brasileiros no Domain Intelligence e no
  Requirement Matcher, incluindo CRM, CRO, CRF, COREN, CREFITO, CRN, CRMV, CRP, CREF, CRTR, CREA,
  CAU, CFT, CRT, CRQ, OAB, CRC, CRA, CORECON, CRB, CRESS, CONRERP, CRECI, CRBio e MTE/DRT.
- Classificação de MTE/DRT como `professional_registration`, separada de `professional_license`.
- `ProfessionalRegistrationInput` e opção genérica `Outro conselho / Outro registro profissional`
  para cadastro/manual review de registros profissionais.
- Integração incremental `analyze_job_v2` no analyzer atual, mantendo `analyze_job` como fallback
  legado.
- Fixtures multiárea para backend, enfermagem, pedagogia, psicologia, engenharia civil,
  arquitetura, cybersecurity e evidências GitHub/portfolio.
- Testes dedicados para requirement matching, evidence matching, transferable skills, scoring,
  explanation builder, confidence, risk adjustment e engine v2.

### Alterado

- Match Engine 2.0 passa a calcular score por código com pesos para requisitos obrigatórios,
  desejáveis, domínio, senioridade, formação/credenciais, evidências, GitHub/portfolio, ATS,
  preferências e penalidade de risco.
- Registros profissionais obrigatórios ausentes passam a gerar gap crítico e limitam o score,
  sem serem compensados por soft skills ou competências transferíveis.
- Evidências do GitHub Analyzer 2.0 podem contribuir para evidence score e explicação quando
  disponíveis.
- Aliases de domínio passam a inferir categorias quando o requisito chega sem categoria explícita.
- Importação pública de `modules/matching` ficou lazy para evitar ciclos de importação.
- Versão do projeto atualizada para `0.12.0`.

### Segurança

- Sugestões para registros profissionais usam linguagem condicional, como "se possuir" e "se houver
  evidência", sem recomendar invenção de credenciais.
- A engine diferencia match direto de competência transferível e não transforma projeto pessoal em
  experiência corporativa.
- Nenhum comportamento de coleta autenticada, compliance ou exposição de API keys foi alterado.

### Documentação

- Regras de matching, regras multiárea, roadmap, README e docs de desenvolvimento atualizados para
  refletir o Match Engine 2.0 implementado.
- Prompts `match_analysis_evidence_based_v1`, `ats_analysis_v1`, `resume_tailor_v1` e
  `career_advice_v1` revisados para contratos, confidence, anti-fabrication e integração com
  evidências/Match Engine 2.0.

## [0.11.0] - 2026-06-21

### Adicionado

- Módulo `modules/github_analyzer` com cliente GitHub público, modelos Pydantic, tree builder,
  filtros, sampler, dependency graph, context builder, evidence index, schemas, scoring e service.
- Suporte a `GITHUB_TOKEN` opcional no cliente GitHub para aumentar rate limit sem exigir token em
  repositórios públicos simples.
- Registro do prompt `github_repo_analysis_v2` no Prompt Registry, com saída validável por JSON
  Guard/Pydantic.
- Pipeline determinístico de fallback para gerar relatório parcial quando a GitHub API falha ou
  quando só há sinais capturados pela extensão.
- Fixtures e testes unitários para URL parsing, árvore, sampler, dependency graph, context builder,
  evidence index, scoring, service e fallback.

### Alterado

- Local Companion API passa a usar o GitHub Analyzer 2 quando o payload da extensão solicita análise
  por API, mantendo o analyzer antigo de portfólio como fallback.
- A extensão continua leve e apenas sinaliza `analysis_result.use_github_api` para o backend local.
- Arquivos `requirements*.txt` foram movidos para `docs/requirements/`, mantendo a raiz mais limpa.
- Versão do projeto atualizada para `0.11.0`.

### Segurança

- Tokens GitHub são opcionais, lidos por ambiente e não são enviados para a extensão/frontend.
- O scoring aplica trava de segurança quando evidências indicam possível segredo exposto.
- A análise diferencia arquivo presente na árvore de conteúdo realmente lido.
- Nenhum comportamento de coleta autenticada foi alterado.

### Documentação

- Prompt playbook `github_repo_analysis_v2` revisado para refletir o pipeline implementado.
- Docs de GitHub/portfólio e roadmap atualizados para a v0.11.0.

## [0.10.0] - 2026-06-21

### Adicionado

- Base de Prompt Registry com `PromptSpec` versionado, carregamento lazy de prompts e prompts
  iniciais para resume extraction, multi-domain job extraction e domain classification.
- JSON Guard para respostas de IA, incluindo limpeza de Markdown fences, parse de JSON, validação
  Pydantic e detecção de campos com baixa confiança.
- Schemas Pydantic para `ResumeExtractionOutput`, `JobExtractionOutput` e
  `DomainClassificationOutput`, com confidence limitado a `0..1`.
- Base de Domain Intelligence com catálogo multiárea, aliases e classificação determinística para
  software, cybersecurity, engineering, nursing, psychology, pedagogy, architecture, healthcare,
  education, perfis técnicos e perfis generalistas.
- Serviços estruturados de resume, job e domain classification, com execução provider-aware e
  fallback heurístico local.
- Suporte no provider Gemini para extração estruturada por prompt específico sem expor API keys.
- Fixtures fictícias multiárea para currículos e vagas em technology, healthcare, education,
  engineering, architecture, cybersecurity e technical maintenance.

### Alterado

- Versão do projeto atualizada para `0.10.0`.
- `modules/ai` passa a exportar serviços de structured extraction além do fluxo de análise
  existente.
- Parsers existentes permanecem como fallback local e não são substituídos por saída de IA.

### Testes

- Cobertura adicionada para Prompt Registry, JSON Guard, schema de resume extraction, schema de job
  extraction, Domain Intelligence e comportamento de fallback da structured extraction.
- Testes com fake provider garantem que a structured extraction nunca chama uma API real na suíte.

### Segurança

- Saídas de IA continuam consultivas e precisam passar por validação Pydantic antes de entrar em
  fluxos do produto.
- Registros profissionais como COREN, CRP, CREA e CAU são detectados como sinais regulados, não
  inventados.
- Nenhum comportamento de coleta autenticada foi alterado.

## [0.9.1] - 2026-06-21

### Documentation

- alinhado `docs/01-product/roadmap.md` ao estado real da v0.9.0;
- reorganizada a visão do produto para começar pela estratégia multiárea atual;
- registrado o ciclo v0.9.1 como estabilização documental antes da v0.10.0;
- destacado que v0.10.0, v0.11.0 e v0.12.0 são próximos marcos reais;
- mantidas seções antigas como histórico, sem tratá-las como próximos passos atuais.
- reorganizada a navegação da documentação para a v0.9.1;
- adicionadas entradas MkDocs para histórico do roadmap, arquitetura de prompts, Prompt Registry e
  prompt playbooks individuais;
- clarificado o índice da documentação em torno de visão de produto, roadmap, prompts de IA, regras
  de negócio, dados, fontes e marcos de desenvolvimento;
- documentada a limpeza documental da v0.9.1 como preparação para v0.10.0 AI Structured Extraction
  e Domain Intelligence.

## [0.9.0] - 2026-06-14

### Added

- Assistive Browser Extension Companion em Manifest V3 para capturar, analisar e enviar a vaga
  atual ao tracker;
- Local Companion API restrita a `127.0.0.1:8765`, com token opcional, Pydantic e sanitização;
- importação páginada de candidaturas já realizadas, com lote local de até 500 itens;
- ranking no dashboard dos requisitos mais recorrentes nas vagas candidatas;
- calibração de evidências com pesos, limites por tipo, penalidades e feedback útil/não útil;
- aba avançada **Extensão**, perfil profissional ampliado e extração opcional de currículo por
  Gemini com fallback local;
- fixtures fictícias e regressões para extensão, API local, memória e deduplicação.
- analisador de GitHub, repositórios, projetos e portfólios com dez scores;
- amostragem inteligente de arquivos, análise de README e qualidade de commits;
- modos standalone na extensão e conectado ao SotuHire, com evidências de projeto na memória.
- botão **SotuHire AI** injetado em repositórios e perfis públicos do GitHub;
- modal com score, grade, stack, README, commits, recomendações e ações conectadas;
- pacote validado e documentação de públicação para a Chrome Web Store.

### Changed

- tracker, oportunidades, memória e capturas usam identidade estável por URL normalizada ou
  empresa+título semelhante;
- a mesma vaga encontrada em LinkedIn, Gupy, Indeed, InfoJobs, Nube ou outro portal mantém um
  único cartão com todas as URLs e fontes;
- repetir uma importação atualiza ou reutiliza registros existentes em vez de duplicá-los;
- candidaturas antigas analisadas depois pelo SotuHire permanecem no mesmo cartão `applied`;
- Search Intelligence permite abrir queries no navegador e orienta a captura pela extensão.

### Security

- extensão nunca recebe nem armazena a API Key configurada no SotuHire;
- Local Companion API aceita somente clientes loopback e não faz login, não guarda senha e não
  burla CAPTCHA;
- uso de IA na extensão chama apenas o SotuHire local, que decide o provider configurado.
- Gemini standalone é opcional, usa permissão de host opcional e mantém a chave somente no storage
  local da extensão; a chave nunca é enviada ao SotuHire.

## [0.8.0] - 2026-06-14

### Added

- Career Memory local em JSONL para currículo, projetos, preferências, análises, feedbacks,
  oportunidades e eventos do tracker;
- RAG lexical local com score por keywords, tags, tipo e recência;
- evidências rastreáveis na análise e contexto relevante opcional para Gemini;
- perfil profissional persistente, score de completude e preferências inferidas editáveis;
- aba avançada de memória com busca, export/import, feedback e limpeza;
- personalização de Search Intelligence e Hidden Jobs Radar pela memória;
- registro de vagas às quais a pessoa já se candidatou;
- fixtures, exemplos e regressões de memória/RAG.

### Changed

- modo rápido usa memória relevante automaticamente sem expor painéis complexos;
- dashboard mostra métricas de memória e eventos do tracker;
- Gemini pode aprimorar a análise com um resumo relevante somente mediante opt-in explícito.

### Security

- memória permanece local por padrão em `data/memory/`;
- envio de contexto relevante ao Gemini permanece desativado por padrão;
- exportações privadas permanecem ignoradas pelo Git.

### Authenticated collection

- modos explícitos `PUBLIC_SCRAPING`, `MANUAL_URL`, `USER_ASSISTED_CAPTURE` e `AUTHENTICATED_BROWSER`;
- captura assistida da vaga ou públicação atualmente aberta pela pessoa usuária;
- ações para salvar a vaga atual, analisar e enviar ao tracker;
- roadmap dedicado para extensão de captura assistida;
- crawling autorizado via sessão Chromium já autenticada, com presets para vagas e publicações do LinkedIn;
- limites de itens, páginas/rolagens, intervalo e referência local de autorização;
- inicialização automática de navegador dedicado com perfil persistente e diagnóstico da conexão CDP;

### Authenticated collection changes

- a aba de coleta distingue coleta pública automática, URL única, captura assistida e navegador autenticado;
- fontes configuradas persistem o modo de coleta;

### Authenticated collection security

- captura assistida processa somente o conteúdo visível explicitamente fornecido;
- login, CAPTCHA, checkpoints, auto-apply e envio automático não são automatizados;

## [0.7.0] - 2026-06-13

### Added

- coleta pública por URL, listagem genérica, página de carreira e RSS/Atom;
- registry extensível e fontes configuráveis por TOML;
- cache local, rate limit por domínio, logs e deduplicação;
- store local e normalização de oportunidades para `JobPostingSchema`;
- aba de coleta com preview, teste, coleta, filtro, análise e tracker;
- Search Intelligence e Hidden Jobs Radar acionáveis;
- terceiro teste Gemini pelo caminho real da análise;
- fixtures HTML/XML e regressões da pipeline pública;

### Changed

- modo rápido ficou mais compacto e modo avançado ganhou workflow completo;
- chave e modelo Gemini digitados na sessão são usados imediatamente;
- resultado mostra provider, modelo, fallback e motivo;
- fontes públicas de qualquer domínio podem ser testadas quando `robots.txt` permitir;

### Security

- URLs autenticadas não são coletadas;
- coleta pública usa user-agent identificável, limites, cache e revisão humana;
- auto-apply, spam e bypass de bloqueios continuam ausentes;

## [0.6.0] - 2026-06-13

### Added

- diagnóstico tipado e seguro para chamadas Gemini;
- testes Gemini simples e estruturado separados;
- modelos Gemini selecionáveis no wizard;
- modo rápido em página única e Search Intelligence no modo avançado;
- query builder, plano de fontes e Hidden Jobs Radar sem scraping;
- demo completa local e script Playwright para screenshots;
- screenshots reais do app no README;
- regressões de Gemini, modos, busca, screenshots, skills e demo;

### Changed

- payload estruturado Gemini usa um JSON Schema mínimo compatível;
- layout, hero, badges, sidebar, upload, botões e cards foram compactados;
- skills principais são limitadas e tecnologias restantes ficam recolhidas;
- detalhes técnicos aparecem somente no modo avançado ou no wizard;

### Fixed

- teste Gemini confundindo erro de schema com erro de chave/modelo;
- `400 INVALID_ARGUMENT` sem diagnóstico acionável;
- modo rápido e avançado visualmente equivalentes;
- fluxo de demonstração dependente de múltiplos cliques;

### Security

- diagnóstico nunca mostra a chave completa;
- Search Intelligence e Hidden Jobs Radar não fazem scraping nem chamadas de rede;

## [0.5.0] - 2026-06-13

### Added

- setup guiado do Gemini com status de chave/SDK, teste explícito e salvamento local;
- fluxo automático do modo rápido e análise completa de exemplo;
- currículos, vagas e expected outputs fictícios para validação;
- filtros simples no dashboard por recomendação, modalidade, senioridade, risco e data;
- testes de regressão para setup, fluxo, skills, exemplos, histórico e dashboard;

### Changed

- análise local e Gemini passam a usar mensagens principais amigáveis;
- preferências permanecem opcionais e escondidas no modo rápido;
- contadores do currículo passam a refletir fatos úteis e deduplicados;
- histórico passa a guardar modalidade e senioridade sem salvar textos brutos;

### Fixed

- prefixos como `Linguagens:`, `Ferramentas:` e `Hardware/IoT:` em chips técnicos;
- duplicatas normalizadas e soft skills misturadas às skills técnicas;
- necessidade de editar `.env` manualmente para ativar Gemini;
- análise rápida dependente de clique após cada mudança;

### Documentation

- setup local de Gemini, fluxo automático, fixtures e regressões documentados;
- roadmap, README, provider strategy e guias de desenvolvimento atualizados;

## [0.4.2] - 2026-06-13

### Added

- estrutura interna `ResumeSection` e agrupamento semântico de experiências e projetos;
- aliases para headings técnicos, profissionais, projetos selecionados e formação com cursos;
- fixtures fictícios realistas de currículos e vagas;
- testes de blocos semânticos, aliases de ambiente, fallback e rótulos da UI;
- links clicáveis com rótulos compactos e expansão para listas longas;

### Changed

- provider local passa a ser apresentado como `Análise local`, sem expor `mock` na UI;
- `DEFAULT_AI_PROVIDER` e `GEMINI_MODEL` passam a ser as variáveis documentadas;
- `LLM_PROVIDER` e `LLM_MODEL` permanecem como aliases compatíveis;
- resumo local limitado a evidências curtas de formação, objetivo e skills;

### Fixed

- contagem de experiências e projetos baseada em linhas soltas;
- soft skills longas exibidas como um único chip;
- fallback do Gemini escondido ou pouco claro;
- cards excessivos de experiências e projetos na revisão do currículo;

### Documentation

- semântica do parser e hotfix v0.4.2 documentados;
- instalação e configuração do Gemini atualizadas;

## [0.4.1] - 2026-06-12

### Added

- camada `modules/ui/` com componentes, estilos, layout e páginas reutilizáveis;
- cards e chips para dados detectados do currículo e da vaga;
- detecção de email, telefone, cidade, LinkedIn, GitHub, portfólio, soft skills e idiomas;
- detecção de benefícios e alertas de dados ausentes na vaga;
- testes realistas para parsers e helpers da interface;

### Changed

- `app.py` reduzido à orquestração da aplicação;
- tema Streamlit unificado com contraste explícito em fundo escuro;
- primeiro upload de currículo processado automaticamente;
- vaga colada processada automaticamente antes da revisão;
- termos internos como `unknown`, `mock`, modalidades e senioridades traduzidos na UI;
- resultados reorganizados em score cards e tabs internas;
- versão do projeto atualizada para `0.4.1`;

### Fixed

- texto branco e métricas ilegíveis sobre fundo claro;
- labels, inputs e tabs com baixo contraste;
- resumo do currículo contendo texto bruto excessivo;
- links sem protocolo não detectados;
- experiências e projetos existentes exibidos como zero;
- coincidência falsa de skill `Git` causada por links do GitHub;
- modalidade remota no feminino e contratos de estágio, trainee e freela;

### Documentation

- README atualizado para o fluxo v0.4.1;
- hotfix de UI e parsers documentado;
- relação com tracker, histórico e dashboard registrada;

## [0.4.0] - 2026-06-12

### Added

- fluxo guiado em abas com modo rápido e modo avançado;
- parser automático de vagas com cargo, empresa, localização, modalidade, salário, contrato, senioridade e skills;
- parser de currículos TXT, PDF e DOCX;
- revisão assistida dos dados detectados;
- camada de IA estruturada com provider mock/local e Gemini opcional;
- fallback local quando o provider externo não está disponível;
- Resume Tailor com resumo, bullets, ordem de seções, keywords, warnings e evidências;
- exportações de análise em JSON e Markdown;
- exportação do Resume Tailor em Markdown;
- persistência local JSON com confirmação de privacidade;
- Job Tracker com status tipados;
- histórico local e dashboard inicial;
- testes de parsers, provider, exporters, storage, tracker e dashboard;

### Changed

- interface Streamlit redesenhada para parecer produto;
- `DEFAULT_AI_PROVIDER` alterado para `mock`;
- dependências PDF/DOCX mantidas leves;
- versão do projeto atualizada para `0.4.0`;

### Fixed

- fluxo excessivamente manual da v0.1;
- ausência de histórico e métricas;
- ausência de fallback estruturado para IA;

### Documentation

- roadmap consolidado até v0.4;
- arquitetura de parsers e storage documentada;
- auditoria de prontidão v0.4;
- README, MkDocs e guias de desenvolvimento atualizados.

## [0.1.0] - 2026-06-12

### Added

- schemas Pydantic para análise, preferências, Resume Tailor e JSON Resume;
- análise currículo x vaga com Match Score e gaps;
- Opportunity Fit Score baseado em preferências;
- ATS Score simples e explicável;
- Risk Score e recomendação determinística;
- Resume Tailor em modo sugestão;
- regras anti-invenção apoiadas por evidências;
- interface Streamlit do MVP Core;
- testes focados para schemas e regras de negócio;

### Changed

- dependências padrão mantidas leves para a v0.1;
- roadmap alinhado ao SotuHire v0.1 — MVP Core;

### Fixed

- ordenação de imports detectada pelo Ruff;
- navegação MkDocs para documentos importantes;
- inconsistências entre README, roadmap e implementação atual;

### Documentation

- documentação revisada e expandida sem reduzir docs existentes;
- README atualizado com visão, limites, arquitetura, comandos e status;
- auditoria de prontidão v0.1;
- metadados, tópicos GitHub e hashtags recomendados.
