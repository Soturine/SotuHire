# Mapa de integração de módulos

Estado atual da `main`, validado em 12 de julho de 2026. O commit inicial da auditoria foi
`309f9662f1da410349d85fefdcacff8778cea51e`; a referência verificável por capacidade está na
[matriz de integração atual](integration-capability-matrix.md).

Este mapa registra como `apps/web`, FastAPI, Local Companion, extensão e `modules/` se conectam
sem mover regra de negócio para o frontend.

```text
apps/web (React/Vite)
  -> apps/api/routes
  -> apps/api/services
  -> modules/*
  -> data local ignorado pelo Git quando há persistência
```

O frontend mostra estado, modo Demo/API Real, badges de provider e warnings. O backend/core calcula
scores, valida evidências, aplica regras anti-invenção e decide fallback.

## Matriz principal

| Funcionalidade | Tela frontend | Endpoint API | Service backend | Módulo core | Status real |
| --- | --- | --- | --- | --- | --- |
| Currículo | `/resume` | `POST /api/v1/resume/extract` | `extract_resume` | `modules/parsers`, structured extractor | Real |
| Vaga | `/job` | `POST /api/v1/job/extract` | `extract_job` | `modules/parsers`, structured extractor | Real |
| Career Context Engine | vários fluxos | consumo interno | services API | `modules/context`, `modules/profile`, `modules/memory` | Real |
| Compatibilidade | `/match` | `POST /api/v1/match/analyze` | `analyze_match` | `modules/analyzer`, `modules/matching` | Real |
| ATS | `/ats` | `POST /api/v1/ats/analyze` | `analyze_ats` | `modules/ats` | Real |
| Tailor | `/tailor` | `POST /api/v1/resume/tailor` | `tailor_resume` | `modules/resume_tailor` | Real |
| GitHub | `/github` | `POST /api/v1/github/repo/analyze` | `analyze_github_repo` | `modules/github_analyzer`, `modules/portfolio` | Real |
| Tracker | `/tracker` | `GET/POST/PATCH /api/v1/tracker/jobs` | `apps.api.services.tracker` | `modules/tracker`, `modules/storage` | Real |
| Dados e privacidade | `/privacy` | `/api/v1/data/health`, `/backups`, `/restore` | `apps.api.services.data` | `modules/storage` | Real |
| Intelligence | `/intelligence` | `/api/v1/tracker/metrics`, `/requirements`, `/funnel`, `/sources` | tracker service | `modules/tracker` | Real |
| IA e Providers | `/settings` | `/api/v1/settings/ai*` | `apps.api.services.ai_settings` | `modules/ai/providers`, `modules/ai/model_catalog.py` | Real v1.9.4 |
| Caixa de Entrada de Oportunidades | `/sources` | `/api/v1/sources/imports*`, `/captures*`, `/dedupe`, `/stats`, `/export`, `/directory` | `apps.api.services.sources` | `modules/sources`, `modules/parsers`, `modules/tracker` | Real |
| Radar de Vagas | `/radar` | `/api/v1/radar/*` | `apps.api.services.radar` | `modules/radar`, `modules/scraping`, `modules/sources`, `modules/tracker` | Real |
| Wishlist com IA/local | `/radar` | `POST /api/v1/radar/wishlists/draft` | `radar_draft_wishlist` | `modules/radar/wishlist_draft.py`, `modules/profile/context.py`, Prompt Registry | Real |
| Perfil Profissional Universal | `/profile` | `/api/v1/profile*` | `apps.api.services.profile` | `modules/profile` | Real |
| Acadêmico / Lattes | `/profile` | `/api/v1/profile/import-lattes`, `/lattes/draft`, `/lattes/confirm` | `apps.api.services.profile` | `modules/academic`, `modules/profile`, `modules/context` | Real |
| Extensão Local | `/sources` | `/api/v1/extension/*` | `apps.api.services.extension` | `modules/local_api`, `browser-extension/` | Real |
| Navegador autenticado autorizado | `/sources` | `/api/v1/sources/authenticated-browser/*` | `apps.api.services.sources` | fluxo existente de scraping local | Parcial |
| Captura assistida autenticada | `/sources` | `POST /api/v1/sources/authenticated-captures` | `apps.api.services.sources` | `modules/sources`, `modules/profile` | Real |
| Streamlit | legado/dev | Não é API web | `app.py`, `modules/ui` | core antigo | Legado |
| Editais / Concursos | `/public-exams` | `/api/v1/public-exams/*` | `apps.api.services.public_exams` | `modules/public_exams`, `modules/context`, `modules/profile` | Fundação real com IA/fallback v1.9.4 |

## Editais e concursos v1.9.3

Endpoints FastAPI:

```txt
POST   /api/v1/public-exams/import
GET    /api/v1/public-exams
GET    /api/v1/public-exams/{notice_id}
DELETE /api/v1/public-exams/{notice_id}
POST   /api/v1/public-exams/{notice_id}/confirm
POST   /api/v1/public-exams/{notice_id}/analyze
POST   /api/v1/public-exams/{notice_id}/study-plan
```

`modules/public_exams` centraliza modelos, parser local, store, scoring, checklist e plano de estudo:

- `ExamNotice`, `ExamRole`, `ExamRequirement`, `ExamTimeline`, `ExamSubject`, `ExamFitScore` e `StudyPlanDraft`;
- importação por texto colado, sem PDF/HTML direto nesta versão;
- IA Gemini/OpenAI opcional pelo prompt `public_exam_notice_extractor_v1`, sempre como rascunho revisável;
- fallback local obrigatório quando a IA falha, vem vazia ou não está configurada;
- confirmação manual antes de salvar em `data/public_exams/notices.json`;
- análise com `CareerContextPurpose.PUBLIC_EXAMS`, Perfil Profissional Universal e evidências acadêmicas/Lattes confirmadas;
- Radar e Tracker preparados para oportunidade pública sem tratar edital como vaga privada.

O fluxo não faz inscrição automática, pagamento, boleto, envio de documentos, login em banca/órgão, scraping autenticado ou CAPTCHA bypass. O endpoint `/api/v1/sources/authenticated-browser/collect` permanece fora do escopo de alteração.

## IA, providers e catálogo de modelos v1.9.4

`apps/api/services/ai_settings.py` seleciona o runtime por preset, provider e modelo salvo:

- `local`: fallback local determinístico.
- `gemini`: `GeminiProvider` com chave e modelo salvos no backend local.
- `openai`: `OpenAIProvider` com chave e modelo salvos no backend local.
- `openai_future`: alias legado normalizado para `openai`.

Endpoints:

```txt
GET  /api/v1/settings/ai/providers
GET  /api/v1/settings/ai/models?provider=gemini
GET  /api/v1/settings/ai/models?provider=openai
POST /api/v1/settings/ai/models/refresh
```

O catálogo usa lista builtin, cache local e refresh opcional via provider. Segredos não entram nas respostas.

## Roteamento de IA

`apps/api/services/ai_settings.py` seleciona o runtime por área:

- `use_ai=false`, provider `local` ou toggle desligado: provider local determinístico.
- `provider=gemini`, chave salva no backend e toggle ligado: Gemini via Prompt Registry.
- `provider=openai`, chave salva no backend e toggle ligado: OpenAI via Prompt Registry.
- falha de provider: fallback local com warning.
- `openai_future`: compatibilidade com dados antigos, normalizada para `openai`.

Toggles atuais:

```txt
allow_match
allow_ats
allow_tailor
allow_github
allow_resume
allow_job
allow_source_import
allow_radar
allow_public_exams
allow_extension
allow_memory_context
```

Currículo, vaga, importações, Radar e o rascunho de editais usam IA quando `use_ai=true` e `provider=gemini` ou `provider=openai` está configurado.
A UI mostra provider, modo e baixa confiança sem expor segredo.

## Ponte da extensão

Endpoints FastAPI:

```txt
GET  /api/v1/extension/status
GET  /api/v1/extension/captures
GET  /api/v1/extension/context
GET  /api/v1/extension/profile-analysis
POST /api/v1/extension/captures/{capture_id}/profile-candidates
POST /api/v1/extension/captures/{capture_id}/add-to-profile
POST /api/v1/extension/projects/{project_id}/profile-candidates
POST /api/v1/extension/projects/{project_id}/add-to-profile
POST /api/v1/extension/import/job
POST /api/v1/extension/import/public-exam
POST /api/v1/extension/import/github
POST /api/v1/extension/import/tracker
PATCH /api/v1/extension/captures/{capture_id}
```

A ponte lê o store local da Local Companion API e permite importar capturas para Vaga, GitHub ou
Candidaturas. Ela não reimplementa crawler logado, não controla contas de terceiros e não altera o
browser autenticado existente.

Na v1.9.4, capturas com `kind=public_exam` podem ser importadas para `/public-exams` como rascunho revisável. A extensão também expõe um contexto seguro com resumo curto do Perfil Universal, fluxos habilitados e status de IA, sem entregar perfil inteiro, memória completa ou API key.

## Importadores e histórico v1.7.1

Endpoints FastAPI:

```txt
GET    /api/v1/sources/imports
POST   /api/v1/sources/imports/text
POST   /api/v1/sources/imports/url
POST   /api/v1/sources/imports/csv
POST   /api/v1/sources/imports/json
GET    /api/v1/sources/captures
PATCH  /api/v1/sources/captures/{capture_id}
POST   /api/v1/sources/captures/{capture_id}/import-job
POST   /api/v1/sources/captures/{capture_id}/save-tracker
POST   /api/v1/sources/captures/{capture_id}/merge
POST   /api/v1/sources/dedupe
GET    /api/v1/sources/directory
POST   /api/v1/sources/export
GET    /api/v1/sources/stats
```

`modules/sources/imports.py` centraliza o store local de fontes e capturas:

- `JobSource`: fonte configurada ou observada;
- `JobImport`: evento de importação;
- `CaptureRecord`: registro persistente da oportunidade;
- `OpportunityInboxItem`: item exibido na Caixa de Entrada;
- `ImportBatch`: resumo de importação CSV/JSON/texto/link;
- `DuplicateCandidate`: possível duplicata explicável.
- `JobSourceDirectory`: fonte pública/oficial/manual segura para descoberta futura.
- `SourceExportResult`: payload local de exportação CSV/JSON.

O fluxo usa parser local para extrair vaga, preserva texto original, normaliza dedupe key e conecta
o item ao tracker quando a pessoa escolhe **Salvar em Candidaturas**. A v1.7.1 permite IA opcional
para enriquecer tags, domínio, senioridade e resumo via `source_import_enrichment_v1`, sempre com
fallback local e sem retornar segredo ao frontend.

## Radar de Vagas v1.8.0

Endpoints FastAPI:

```txt
GET    /api/v1/radar/wishlists
POST   /api/v1/radar/wishlists
PATCH  /api/v1/radar/wishlists/{wishlist_id}
DELETE /api/v1/radar/wishlists/{wishlist_id}
GET    /api/v1/radar/sources
POST   /api/v1/radar/sources
PATCH  /api/v1/radar/sources/{source_id}
DELETE /api/v1/radar/sources/{source_id}
POST   /api/v1/radar/run
GET    /api/v1/radar/runs
GET    /api/v1/radar/results
PATCH  /api/v1/radar/results/{result_id}
POST   /api/v1/radar/results/{result_id}/save-inbox
POST   /api/v1/radar/results/{result_id}/save-tracker
GET    /api/v1/radar/alerts
PATCH  /api/v1/radar/alerts/{alert_id}
GET    /api/v1/radar/stats
```

`modules/radar` centraliza wishlists, fontes, rodadas, resultados e alertas em JSON local. O Radar
consulta RSS/Atom público em rodada manual, prepara adapters de APIs oficiais, calcula score local e
conecta resultados revisados à Caixa de Entrada ou ao Tracker.

O prompt `job_radar_match_explanation_v1` é opcional e só explica evidências/lacunas. Score final,
deduplicação e alertas permanecem no backend.

## Wishlist e contexto v1.8.1

Endpoint novo:

```txt
POST /api/v1/radar/wishlists/draft
```

Esse endpoint recebe texto livre, monta um rascunho de `JobWishlist` e retorna:

- `wishlist`;
- `confidence`;
- `detected_domains`;
- `detected_career_moments`;
- `assumptions`;
- `questions_to_confirm`;
- `warnings`;
- `needs_user_review=true`;
- `provider_used`;
- `analysis_mode`.

O rascunho não é persistido. O frontend apenas preenche o formulário editável, e a pessoa precisa
salvar manualmente.

`modules/profile/context.py` e `modules/profile/orchestrator.py` preparam um contexto profissional
universal, sem assumir tecnologia, GitHub, CLT, graduação, conselho profissional ou experiência
formal. A v1.8.1 usava esse contexto apenas como sinal opcional; a v1.8.2 transforma essa base no
Perfil Profissional Universal persistido.

## Perfil Profissional Universal v1.8.2

Endpoints FastAPI:

```txt
GET    /api/v1/profile
PUT    /api/v1/profile
POST   /api/v1/profile/items
PATCH  /api/v1/profile/items/{item_id}
DELETE /api/v1/profile/items/{item_id}
POST   /api/v1/profile/import-text
POST   /api/v1/profile/import-lattes
POST   /api/v1/profile/lattes/draft
POST   /api/v1/profile/lattes/confirm
POST   /api/v1/profile/deduplicate
GET    /api/v1/profile/context
```

`modules/profile` agora centraliza o perfil local:

- `models.py`: perfil, item, source summary, estado multi-perfil futuro e draft de importação;
- `store.py`: persistência local em `data/profile/profiles.json`;
- `service.py`: CRUD, importação local e deduplicação;
- `extraction.py`: fallback local multiárea;
- `orchestrator.py`: monta `ProfileContext` a partir do perfil persistido ou do store legado.

O prompt `profile_items_extractor_v1` é opcional e sempre retorna itens para revisão humana. O
frontend `/profile` permite editar dados básicos, adicionar item manual, filtrar por tipo, editar
evidências, importar texto e revisar drafts.

O fluxo **Acadêmico / Lattes** usa `modules/academic` para transformar texto colado em candidatos
revisáveis de `ProfileItem`. Gemini pode atuar como extrator assistido quando configurado, mas a
resposta sempre exige revisão humana e cai para parser local quando falha.

O `CareerContextEngine` usa `ProfileContextOrchestrator` e `MemoryRetriever` para entregar um
contexto compacto por propósito. Wishlist, Radar, Scheduler, Match, ATS, Tailor, Tracker, Fontes,
Notificações, Extensão, Lattes/acadêmico e GitHub/Portfólio consultam essa camada. Dados do
perfil/memória só entram em provider externo quando `allow_memory_context=true`; evidências
sensíveis são omitidas do payload externo.

Capturas e projetos da extensão agora podem gerar candidatos revisáveis de `ProfileItem` com
`source_ref` local. Nada é salvo no Perfil Universal antes de confirmação humana.

Leia também [Career Context Engine](career-context-engine.md), [Extension Profile Bridge](extension-profile-bridge.md) e [Fundação para Editais e Concursos](public-exams-foundation.md).

## Captura Assistida Autenticada v1.8.2

Endpoint FastAPI:

```txt
POST /api/v1/sources/authenticated-captures
```

Esse endpoint salva texto visível ou selecionado de uma página autenticada como item de Caixa de
Entrada, sempre com revisão humana. Ele não altera o fluxo existente de Chromium/CDP e rejeita
metadata com chaves de cookie, token, sessão, headers ou segredos.

A captura pode adicionar sinais locais derivados do Perfil Profissional:

- itens confirmados encontrados no texto visível;
- possíveis gaps de registros profissionais citados na vaga;
- baixa confiança quando a captura não encontra evidência suficiente.

## UX web v1.6.0

- Home e Dashboard exibem fluxo guiado de 8 passos.
- Currículo, Vaga, Match, ATS, Tailor e GitHub exibem estado Local/IA/Fallback.
- Match, ATS, Tailor e GitHub separam pontos fortes, lacunas, sugestões práticas, riscos, próximas
  ações e itens que não devem ser adicionados sem evidência.
- Fontes e Captura mostra status do companion, últimas capturas, origem, data, tipo e ações.
- Kanban mostra origem, score, última análise, notas e data.

## Incrementos v1.6.0

- Match, ATS, Tailor e GitHub adicionam explicabilidade de recomendacao, evidencias usadas,
  prioridade de melhoria e botoes de copiar sugestoes/plano de acao.
- O Kanban envia status reais do backend, usa drag-and-drop com rollback quando a API falha e mantem
  alternativa por select para teclado/mobile.
- A ponte da extensao inclui `kind`, `source` e `captured_at` para historico seguro de capturas.
- Playwright cobre Chromium, Firefox e WebKit; responsividade mobile/tablet/desktop e capturas
  visuais padronizadas rodam uma vez no Chromium.

## Incrementos v1.7.0

- Fontes e Captura ganhou Caixa de Entrada para texto, link, CSV, JSON e capturas locais.
- Deduplicacao local usa URL normalizada, empresa+cargo+localidade e texto normalizado.
- Importador de URL faz apenas leitura publica simples e orienta colar texto quando houver bloqueio
  ou login.
- Tracker preserva origem/fonte ao salvar oportunidades importadas.
- Docs de fontes publicas deixam crawler amplo, busca massiva, login automatico e auto-apply fora
  do escopo.

## Incrementos v1.7.1

- Upload CSV/JSON pelo navegador com preview e confirmacao.
- Mescla visual de duplicatas preservando historico e origem.
- Exportacao local da Caixa de Entrada em CSV/JSON.
- Diretório de Fontes para preparar paginas abertas, feeds, APIs oficiais, CSV/JSON recorrente e
  links manuais sem crawler amplo.
- Teste anti-mojibake em textos publicos.

## Incrementos v1.8.0

- Nova tela `/radar` com Resumo, Wishlist, Fontes, Rodadas, Resultados e Alertas.
- Backend `modules/radar` com store local, execução manual e limites por rodada.
- RSS/Atom público implementado como fonte segura.
- APIs oficiais ficam estruturadas como adapters planejados.
- Resultados do Radar podem ser salvos na Caixa de Entrada ou em Candidaturas.
- Alertas locais indicam vagas acima do score mínimo da wishlist.
