# Matriz de capacidades e integração

Esta matriz é gerada a partir de `config/capabilities.json` e confrontada com o OpenAPI real, as rotas TanStack e os arquivos de testes e documentação.

**Commit-base da última verificação:** `309f9662f1da410349d85fefdcacff8778cea51e`

## Resumo

| ID | Capacidade | Frontend | API | Perfil/contexto | IA | Extensão | Snapshot | Status | Lacunas |
|---|---|---|---:|---|---|---|---|---|---|
| resume_extraction | Currículo Mestre | `/resume` | 1 | sem contexto dedicado | resume_extraction_v1 | A extensão não envia currículos; o fluxo permanece no site/API local. | ResumeSnapshot disponível na camada de storage quando a candidatura registra o currículo usado. | complete | A extração isolada não persiste automaticamente uma variante de currículo. |
| job_extraction | Leitura de vaga | `/job` | 1 | sem contexto dedicado | job_extraction_multi_domain_v1 | Capturas de vaga podem ser importadas pelo bridge da extensão. | JobSnapshot imutável disponível para captura e Tracker. | complete | nenhuma registrada |
| match | Compatibilidade | `/match` | 1 | match | match_analysis_evidence_based_v1 | Vagas capturadas podem ser encaminhadas ao fluxo de Match pelo site. | AnalysisSnapshot pode vincular vaga e currículo usados. | complete | nenhuma registrada |
| ats | Análise ATS | `/ats` | 1 | ats | ats_analysis_v1 | Sem execução ATS direta no content script; a análise ocorre no backend/site. | AnalysisSnapshot ATS pode ser associado a uma candidatura. | complete | nenhuma registrada |
| resume_tailor | Adaptação segura de currículo | `/tailor` | 1 | tailor | resume_tailor_v1 | O site pode adaptar currículo para uma vaga capturada, sem auto-apply. | ResumeSnapshot da variante adaptada pode ser vinculado ao Tracker. | complete | Exportação avançada de variantes permanece no roadmap de Resume Studio. |
| universal_profile | Perfil Profissional Universal | `/profile` | 7 | generic | profile_items_extractor_v1, profile_lattes_extractor_v1 | Capturas GitHub e outras evidências viram candidatos revisáveis, nunca fatos automáticos. | ResumeSnapshot referencia os ProfileItems utilizados; o perfil em si permanece editável. | complete | Alguns módulos legados ainda mantêm stores próprios e são tratados pela migração gradual. |
| public_exams | Editais e concursos | `/public-exams` | 5 | public_exams | public_exam_notice_extractor_v1 | A extensão captura texto público e importa o edital pelo bridge local. | PublicExamSnapshot imutável preserva texto, estrutura, requisitos e cronograma. | complete | nenhuma registrada |
| radar | Radar, wishlist e agendamentos | `/radar` | 7 | radar | job_wishlist_builder_v1, job_radar_match_explanation_v1 | Resultados podem chegar ao Tracker; a extensão não executa o scheduler. | Ao salvar no Tracker, a oportunidade pode gerar JobSnapshot. | complete | Conectores oficiais adicionais permanecem fora desta capacidade atual. |
| tracker | Tracker e histórico de candidaturas | `/tracker` | 5 | tracker | não | Capturas podem ser importadas como candidaturas com source_capture_id. | Vincula snapshots de vaga, currículo, variante, Match e ATS quando disponíveis. | complete | Registros legados sem texto original permanecem sem snapshot inventado. |
| github_portfolio | GitHub e portfólio | `/github` | 2 | github | github_repo_analysis_v2 | Modo independente e integrado analisam repositórios públicos e exibem relatório estruturado. | AiRun registra a execução; o ProjectAnalysisStore legado ainda não possui snapshot imutável dedicado. | partial | Análise agregada do perfil GitHub ainda não possui prompt consumido pelo runtime principal.; O relatório de projeto legado ainda não possui snapshot imutável dedicado. |
| sources_capture | Fontes e captura assistida | `/sources` | 6 | sources | source_import_enrichment_v1 | A página exibe capturas do Local Companion e permite importar para módulos do site. | Capturas importadas como vagas ou editais criam snapshots nos fluxos correspondentes. | complete | nenhuma registrada |
| extension_bridge | Extensão e Local Companion | `/sources` | 7 | extension | github_repo_analysis_v2 | Handshake, modo independente, modo conectado, fila offline e importação explícita. | Capturas de vaga, edital e análise geram snapshots imutáveis no companion. | complete | Compatibilidade depende de manter manifesto, extensão e companion versionados em conjunto. |
| ai_settings | Configuração de IA | `/settings` | 7 | sem contexto dedicado | não | A configuração do site não lê nem persiste a chave própria da extensão. | AiRunStore registra metadados seguros; segredos não entram em snapshots. | complete | nenhuma registrada |
| notifications | Notificações locais | `/dashboard` | 4 | sem contexto dedicado | não | A extensão não recebe notificações do site. | A notificação referencia a origem; não é um snapshot de conteúdo. | complete | Não existe rota exclusiva; o resumo é exibido no Dashboard e no Radar. |
| data_reliability | Persistência, migração, backup e saúde dos dados | `/privacy` | 5 | sem contexto dedicado | não | Backups não incluem chrome.storage, IndexedDB, chaves, tokens ou cookies. | Tabelas e triggers impedem UPDATE/DELETE de snapshots imutáveis. | complete | nenhuma registrada |

## Contratos por capacidade

### Currículo Mestre (`resume_extraction`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `resume_extraction` |
| `frontend_route` | `/resume` |
| `api_endpoints` | `POST /api/v1/resume/extract` |
| `backend_services` | `apps/api/services/analysis.py` |
| `core_modules` | `modules/ai/structured_resume_extractor.py`<br>`modules/parsers/resume_parser.py` |
| `stores` | `modules/profile/store.py` |
| `profile_integration` | A extração pode alimentar o Perfil Universal somente após ação explícita da pessoa usuária. |
| `context_purpose` | — |
| `ai_support` | enabled=true; prompts=resume_extraction_v1; providers=gemini, openai, local; fallback=Parser local de currículo |
| `extension_support` | A extensão não envia currículos; o fluxo permanece no site/API local. |
| `dedupe_strategy` | Itens importados são deduplicados no Perfil Universal por identidade e source_ref. |
| `snapshot_support` | ResumeSnapshot disponível na camada de storage quando a candidatura registra o currículo usado. |
| `tests` | `tests/test_api_resume.py`<br>`tests/test_structured_resume_extractor.py` |
| `docs` | `docs/02-architecture/parsers.md`<br>`docs/04-ai/prompts/resume-extraction-v1.md` |
| `status` | `complete` |
| `gaps` | A extração isolada não persiste automaticamente uma variante de currículo. |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Leitura de vaga (`job_extraction`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `job_extraction` |
| `frontend_route` | `/job` |
| `api_endpoints` | `POST /api/v1/job/extract` |
| `backend_services` | `apps/api/services/analysis.py` |
| `core_modules` | `modules/ai/structured_job_extractor.py`<br>`modules/parsers/job_description_parser.py` |
| `stores` | `modules/opportunities/opportunity_store.py`<br>`modules/storage/snapshots.py` |
| `profile_integration` | A extração da vaga não altera o perfil; ela fornece requisitos para análises posteriores. |
| `context_purpose` | — |
| `ai_support` | enabled=true; prompts=job_extraction_multi_domain_v1; providers=gemini, openai, local; fallback=Parser local multiárea e classificador determinístico |
| `extension_support` | Capturas de vaga podem ser importadas pelo bridge da extensão. |
| `dedupe_strategy` | URL canônica e identidade da oportunidade removem parâmetros de rastreamento. |
| `snapshot_support` | JobSnapshot imutável disponível para captura e Tracker. |
| `tests` | `tests/test_api_job.py`<br>`tests/test_structured_job_extractor.py` |
| `docs` | `docs/02-architecture/parsers.md`<br>`docs/04-ai/prompts/job-extraction-multi-domain-v1.md` |
| `status` | `complete` |
| `gaps` | nenhuma registrada |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Compatibilidade (`match`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `match` |
| `frontend_route` | `/match` |
| `api_endpoints` | `POST /api/v1/match/analyze` |
| `backend_services` | `apps/api/services/analysis.py` |
| `core_modules` | `modules/matching/engine.py`<br>`modules/context/engine.py` |
| `stores` | `modules/memory/memory_store.py`<br>`modules/storage/ai_runs.py`<br>`modules/storage/snapshots.py` |
| `profile_integration` | Consulta Perfil Universal e evidências locais sem promover inferências a fatos. |
| `context_purpose` | `match` |
| `ai_support` | enabled=true; prompts=match_analysis_evidence_based_v1; providers=gemini, openai, local; fallback=Match Engine determinístico baseado em evidências |
| `extension_support` | Vagas capturadas podem ser encaminhadas ao fluxo de Match pelo site. |
| `dedupe_strategy` | Evidências são deduplicadas por source_ref e conteúdo normalizado. |
| `snapshot_support` | AnalysisSnapshot pode vincular vaga e currículo usados. |
| `tests` | `tests/test_api_match.py`<br>`tests/test_match_engine_v2.py` |
| `docs` | `docs/03-business-rules/matching-rules.md`<br>`docs/04-ai/prompts/match-analysis-evidence-based-v1.md` |
| `status` | `complete` |
| `gaps` | nenhuma registrada |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Análise ATS (`ats`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `ats` |
| `frontend_route` | `/ats` |
| `api_endpoints` | `POST /api/v1/ats/analyze` |
| `backend_services` | `apps/api/services/analysis.py` |
| `core_modules` | `modules/ats/ats_score.py`<br>`modules/context/engine.py` |
| `stores` | `modules/storage/ai_runs.py`<br>`modules/storage/snapshots.py` |
| `profile_integration` | Usa apenas evidências confirmadas do Perfil/Career Context para sugerir termos seguros. |
| `context_purpose` | `ats` |
| `ai_support` | enabled=true; prompts=ats_analysis_v1; providers=gemini, openai, local; fallback=Revisão local de palavras-chave baseada no Match |
| `extension_support` | Sem execução ATS direta no content script; a análise ocorre no backend/site. |
| `dedupe_strategy` | Palavras-chave são normalizadas e únicas antes da revisão. |
| `snapshot_support` | AnalysisSnapshot ATS pode ser associado a uma candidatura. |
| `tests` | `tests/test_api_ats.py`<br>`tests/test_ats_score.py` |
| `docs` | `docs/03-business-rules/ats-rules.md`<br>`docs/04-ai/prompts/ats-analysis-v1.md` |
| `status` | `complete` |
| `gaps` | nenhuma registrada |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Adaptação segura de currículo (`resume_tailor`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `resume_tailor` |
| `frontend_route` | `/tailor` |
| `api_endpoints` | `POST /api/v1/resume/tailor` |
| `backend_services` | `apps/api/services/analysis.py` |
| `core_modules` | `modules/resume_tailor/tailor_rules.py`<br>`modules/context/engine.py` |
| `stores` | `modules/storage/snapshots.py`<br>`modules/storage/ai_runs.py` |
| `profile_integration` | Usa evidências confirmadas e nunca transforma sugestão em experiência declarada. |
| `context_purpose` | `tailor` |
| `ai_support` | enabled=true; prompts=resume_tailor_v1; providers=gemini, openai, local; fallback=Regras locais de adaptação com bloqueios anti-invenção |
| `extension_support` | O site pode adaptar currículo para uma vaga capturada, sem auto-apply. |
| `dedupe_strategy` | Sugestões e palavras-chave são normalizadas antes da apresentação. |
| `snapshot_support` | ResumeSnapshot da variante adaptada pode ser vinculado ao Tracker. |
| `tests` | `tests/test_api_tailor.py`<br>`tests/test_resume_tailor_rules.py` |
| `docs` | `docs/03-business-rules/resume-tailor-rules.md`<br>`docs/04-ai/prompts/resume-tailor-v1.md` |
| `status` | `complete` |
| `gaps` | Exportação avançada de variantes permanece no roadmap de Resume Studio. |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Perfil Profissional Universal (`universal_profile`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `universal_profile` |
| `frontend_route` | `/profile` |
| `api_endpoints` | `GET /api/v1/profile`<br>`PUT /api/v1/profile`<br>`POST /api/v1/profile/items`<br>`POST /api/v1/profile/import-text`<br>`POST /api/v1/profile/lattes/draft`<br>`POST /api/v1/profile/lattes/confirm`<br>`GET /api/v1/profile/context` |
| `backend_services` | `apps/api/services/profile.py` |
| `core_modules` | `modules/profile/service.py`<br>`modules/profile/orchestrator.py`<br>`modules/academic/lattes_service.py` |
| `stores` | `modules/profile/store.py`<br>`modules/memory/memory_store.py` |
| `profile_integration` | É a fonte central de fatos confirmados; candidatos extraídos exigem revisão explícita. |
| `context_purpose` | `generic` |
| `ai_support` | enabled=true; prompts=profile_items_extractor_v1, profile_lattes_extractor_v1; providers=gemini, openai, local; fallback=Extratores locais de perfil e Lattes |
| `extension_support` | Capturas GitHub e outras evidências viram candidatos revisáveis, nunca fatos automáticos. |
| `dedupe_strategy` | Identidade canônica por tipo, source_ref forte e conteúdo normalizado. |
| `snapshot_support` | ResumeSnapshot referencia os ProfileItems utilizados; o perfil em si permanece editável. |
| `tests` | `tests/test_api_profile.py`<br>`tests/test_academic_lattes.py` |
| `docs` | `docs/02-architecture/career-context-engine.md`<br>`docs/02-architecture/data-lineage-and-deduplication.md` |
| `status` | `complete` |
| `gaps` | Alguns módulos legados ainda mantêm stores próprios e são tratados pela migração gradual. |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Editais e concursos (`public_exams`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `public_exams` |
| `frontend_route` | `/public-exams` |
| `api_endpoints` | `POST /api/v1/public-exams/import`<br>`GET /api/v1/public-exams`<br>`POST /api/v1/public-exams/{notice_id}/confirm`<br>`POST /api/v1/public-exams/{notice_id}/analyze`<br>`POST /api/v1/public-exams/{notice_id}/study-plan` |
| `backend_services` | `apps/api/services/public_exams.py` |
| `core_modules` | `modules/public_exams/service.py`<br>`modules/public_exams/store.py` |
| `stores` | `modules/public_exams/store.py`<br>`modules/storage/snapshots.py` |
| `profile_integration` | Compara requisitos com evidências confirmadas e mantém revisão humana. |
| `context_purpose` | `public_exams` |
| `ai_support` | enabled=true; prompts=public_exam_notice_extractor_v1; providers=gemini, openai, local; fallback=Parser local de edital e cálculo determinístico de aderência |
| `extension_support` | A extensão captura texto público e importa o edital pelo bridge local. |
| `dedupe_strategy` | Número oficial, órgão, banca e identidade de cargo antes da URL. |
| `snapshot_support` | PublicExamSnapshot imutável preserva texto, estrutura, requisitos e cronograma. |
| `tests` | `tests/test_public_exams.py`<br>`tests/test_api_extension_bridge.py` |
| `docs` | `docs/03-business-rules/public-exam-rules.md`<br>`docs/02-architecture/public-exams-foundation.md` |
| `status` | `complete` |
| `gaps` | nenhuma registrada |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Radar, wishlist e agendamentos (`radar`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `radar` |
| `frontend_route` | `/radar` |
| `api_endpoints` | `GET /api/v1/radar/wishlists`<br>`POST /api/v1/radar/wishlists`<br>`POST /api/v1/radar/wishlists/draft`<br>`POST /api/v1/radar/run`<br>`GET /api/v1/radar/results`<br>`GET /api/v1/radar/schedules`<br>`POST /api/v1/radar/schedules` |
| `backend_services` | `apps/api/services/radar.py` |
| `core_modules` | `modules/radar/service.py`<br>`modules/radar/scheduler.py`<br>`modules/context/engine.py` |
| `stores` | `modules/radar/service.py`<br>`modules/radar/schedule_store.py` |
| `profile_integration` | Usa objetivos, preferências e evidências confirmadas para priorizar resultados. |
| `context_purpose` | `radar` |
| `ai_support` | enabled=true; prompts=job_wishlist_builder_v1, job_radar_match_explanation_v1; providers=gemini, openai, local; fallback=Draft e explicação determinísticos |
| `extension_support` | Resultados podem chegar ao Tracker; a extensão não executa o scheduler. |
| `dedupe_strategy` | Resultados usam identidade canônica de oportunidade e URL normalizada. |
| `snapshot_support` | Ao salvar no Tracker, a oportunidade pode gerar JobSnapshot. |
| `tests` | `tests/test_api_radar.py`<br>`tests/test_api_radar_scheduler.py` |
| `docs` | `docs/03-business-rules/job-radar-rules.md`<br>`docs/02-architecture/background-jobs.md` |
| `status` | `complete` |
| `gaps` | Conectores oficiais adicionais permanecem fora desta capacidade atual. |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Tracker e histórico de candidaturas (`tracker`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `tracker` |
| `frontend_route` | `/tracker` |
| `api_endpoints` | `GET /api/v1/tracker/jobs`<br>`POST /api/v1/tracker/jobs`<br>`PATCH /api/v1/tracker/jobs/{record_id}`<br>`GET /api/v1/tracker/metrics`<br>`GET /api/v1/tracker/funnel` |
| `backend_services` | `apps/api/services/tracker.py` |
| `core_modules` | `modules/tracker/job_tracker.py`<br>`modules/storage/applications.py`<br>`modules/storage/snapshots.py` |
| `stores` | `modules/tracker/job_tracker.py`<br>`modules/storage/applications.py` |
| `profile_integration` | Consulta contexto no histórico, sem exigir o perfil para o modo rápido. |
| `context_purpose` | `tracker` |
| `ai_support` | enabled=false; prompts=nenhum; providers=local; fallback=Não aplicável; operações do Tracker são determinísticas |
| `extension_support` | Capturas podem ser importadas como candidaturas com source_capture_id. |
| `dedupe_strategy` | Identidade de candidatura e oportunidade evita reenvio duplicado. |
| `snapshot_support` | Vincula snapshots de vaga, currículo, variante, Match e ATS quando disponíveis. |
| `tests` | `tests/test_api_tracker.py`<br>`tests/test_job_tracker.py`<br>`tests/test_storage_snapshots.py` |
| `docs` | `docs/07-development/job-tracker-kanban.md`<br>`docs/02-architecture/storage-and-history.md` |
| `status` | `complete` |
| `gaps` | Registros legados sem texto original permanecem sem snapshot inventado. |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### GitHub e portfólio (`github_portfolio`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `github_portfolio` |
| `frontend_route` | `/github` |
| `api_endpoints` | `POST /api/v1/github/repo/analyze`<br>`POST /api/v1/extension/import/github` |
| `backend_services` | `apps/api/services/analysis.py`<br>`apps/api/services/extension.py` |
| `core_modules` | `modules/github_analyzer/analyzer_service.py`<br>`modules/portfolio/store.py` |
| `stores` | `modules/portfolio/store.py`<br>`modules/storage/ai_runs.py` |
| `profile_integration` | Relatórios geram candidatos de evidência que exigem confirmação antes de entrar no perfil. |
| `context_purpose` | `github` |
| `ai_support` | enabled=true; prompts=github_repo_analysis_v2; providers=gemini, openai, local; fallback=Analisador heurístico do repositório |
| `extension_support` | Modo independente e integrado analisam repositórios públicos e exibem relatório estruturado. |
| `dedupe_strategy` | Identidade owner/repo e hash do relatório; fontes são preservadas. |
| `snapshot_support` | AiRun registra a execução; o ProjectAnalysisStore legado ainda não possui snapshot imutável dedicado. |
| `tests` | `tests/test_api_github.py`<br>`tests/test_github_analyzer_service.py`<br>`tests/test_extension_github_repo_sampling.py` |
| `docs` | `docs/05-data-sources/github-portfolio-analyzer.md`<br>`docs/04-ai/prompts/github-repo-analysis-v2.md` |
| `status` | `partial` |
| `gaps` | Análise agregada do perfil GitHub ainda não possui prompt consumido pelo runtime principal.; O relatório de projeto legado ainda não possui snapshot imutável dedicado. |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Fontes e captura assistida (`sources_capture`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `sources_capture` |
| `frontend_route` | `/sources` |
| `api_endpoints` | `GET /api/v1/sources/imports`<br>`POST /api/v1/sources/imports/text`<br>`POST /api/v1/sources/imports/url`<br>`GET /api/v1/sources/captures`<br>`POST /api/v1/sources/dedupe`<br>`GET /api/v1/sources/directory` |
| `backend_services` | `apps/api/services/sources.py` |
| `core_modules` | `modules/sources/imports.py`<br>`modules/core/deduplication.py`<br>`modules/context/engine.py` |
| `stores` | `modules/sources/imports.py`<br>`modules/memory/memory_store.py` |
| `profile_integration` | Importações podem gerar evidência revisável e consultar contexto de fontes. |
| `context_purpose` | `sources` |
| `ai_support` | enabled=true; prompts=source_import_enrichment_v1; providers=gemini, openai, local; fallback=Normalização determinística da importação |
| `extension_support` | A página exibe capturas do Local Companion e permite importar para módulos do site. |
| `dedupe_strategy` | URL canônica, identidade da entidade e merge com preservação de fontes. |
| `snapshot_support` | Capturas importadas como vagas ou editais criam snapshots nos fluxos correspondentes. |
| `tests` | `tests/test_api_source_imports.py`<br>`tests/test_opportunity_cross_portal_identity.py` |
| `docs` | `docs/05-data-sources/public-source-importers.md`<br>`docs/02-architecture/opportunity-collection-pipeline.md` |
| `status` | `complete` |
| `gaps` | nenhuma registrada |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Extensão e Local Companion (`extension_bridge`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `extension_bridge` |
| `frontend_route` | `/sources` |
| `api_endpoints` | `POST /api/v1/extension/handshake`<br>`GET /api/v1/extension/status`<br>`GET /api/v1/extension/captures`<br>`GET /api/v1/extension/context`<br>`POST /api/v1/extension/import/job`<br>`POST /api/v1/extension/import/public-exam`<br>`POST /api/v1/extension/import/tracker` |
| `backend_services` | `apps/api/services/extension.py` |
| `core_modules` | `modules/local_api/app.py`<br>`modules/local_api/compatibility.py` |
| `stores` | `modules/local_api/app.py`<br>`modules/storage/snapshots.py` |
| `profile_integration` | Contexto seguro e candidatos de perfil são enviados apenas mediante ações explícitas. |
| `context_purpose` | `extension` |
| `ai_support` | enabled=true; prompts=github_repo_analysis_v2; providers=gemini, openai, local; fallback=Análise local e fila offline; chave própria fica fora do site |
| `extension_support` | Handshake, modo independente, modo conectado, fila offline e importação explícita. |
| `dedupe_strategy` | capture_id, URL normalizada e identidade do payload evitam reenvios duplicados. |
| `snapshot_support` | Capturas de vaga, edital e análise geram snapshots imutáveis no companion. |
| `tests` | `tests/test_api_extension_bridge.py`<br>`tests/test_extension_capture_flow.py`<br>`tests/test_extension_connected_sotuhire_mode.py` |
| `docs` | `docs/02-architecture/local-companion-api.md`<br>`docs/02-architecture/extension-profile-bridge.md` |
| `status` | `complete` |
| `gaps` | Compatibilidade depende de manter manifesto, extensão e companion versionados em conjunto. |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Configuração de IA (`ai_settings`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `ai_settings` |
| `frontend_route` | `/settings` |
| `api_endpoints` | `GET /api/v1/settings/ai`<br>`GET /api/v1/settings/ai/providers`<br>`GET /api/v1/settings/ai/models`<br>`POST /api/v1/settings/ai/models/refresh`<br>`POST /api/v1/settings/ai/test`<br>`POST /api/v1/settings/ai`<br>`DELETE /api/v1/settings/ai` |
| `backend_services` | `apps/api/services/ai_settings.py` |
| `core_modules` | `modules/ai/providers/gemini_provider.py`<br>`modules/ai/providers/openai_provider.py`<br>`modules/ai/prompt_registry.py` |
| `stores` | `apps/api/services/ai_settings.py`<br>`modules/storage/ai_runs.py` |
| `profile_integration` | Permissões controlam quais contextos podem ser usados por cada fluxo de IA. |
| `context_purpose` | — |
| `ai_support` | enabled=true; prompts=nenhum; providers=gemini, openai, local; fallback=Provider local quando o externo está desativado ou indisponível |
| `extension_support` | A configuração do site não lê nem persiste a chave própria da extensão. |
| `dedupe_strategy` | Catálogo de modelos é normalizado por provider e identificador. |
| `snapshot_support` | AiRunStore registra metadados seguros; segredos não entram em snapshots. |
| `tests` | `tests/test_api_ai_settings.py`<br>`tests/test_ai_provider_routing.py` |
| `docs` | `docs/02-architecture/ai-provider-model-catalog.md`<br>`docs/04-ai/provider-strategy.md` |
| `status` | `complete` |
| `gaps` | nenhuma registrada |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Notificações locais (`notifications`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `notifications` |
| `frontend_route` | `/dashboard` |
| `api_endpoints` | `GET /api/v1/notifications`<br>`PATCH /api/v1/notifications/{notification_id}`<br>`POST /api/v1/notifications/mark-all-read`<br>`DELETE /api/v1/notifications/read` |
| `backend_services` | `apps/api/services/notifications.py` |
| `core_modules` | `modules/radar/notifications.py`<br>`modules/radar/scheduler.py` |
| `stores` | `modules/radar/notifications.py` |
| `profile_integration` | As notificações refletem resultados do Radar; não alteram o perfil. |
| `context_purpose` | — |
| `ai_support` | enabled=false; prompts=nenhum; providers=local; fallback=Não aplicável |
| `extension_support` | A extensão não recebe notificações do site. |
| `dedupe_strategy` | Cooldown e identidade do resultado impedem alertas repetidos. |
| `snapshot_support` | A notificação referencia a origem; não é um snapshot de conteúdo. |
| `tests` | `tests/test_api_radar_scheduler.py` |
| `docs` | `docs/02-architecture/background-jobs.md`<br>`docs/07-development/alerts-roadmap.md` |
| `status` | `complete` |
| `gaps` | Não existe rota exclusiva; o resumo é exibido no Dashboard e no Radar. |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

### Persistência, migração, backup e saúde dos dados (`data_reliability`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `data_reliability` |
| `frontend_route` | `/privacy` |
| `api_endpoints` | `GET /api/v1/data/health`<br>`GET /api/v1/data/backups`<br>`POST /api/v1/data/backups`<br>`GET /api/v1/data/backups/{archive_name}`<br>`POST /api/v1/data/restore` |
| `backend_services` | `apps/api/services/data.py`<br>`modules/storage/backup.py`<br>`modules/storage/health.py`<br>`modules/storage/legacy_migration.py` |
| `core_modules` | `modules/storage/database.py`<br>`modules/storage/repositories/base.py`<br>`modules/storage/migrations/runner.py` |
| `stores` | `modules/storage/database.py`<br>`modules/storage/repositories/sqlite_repository.py` |
| `profile_integration` | Migra e protege o perfil e demais entidades sem apagar os stores legados. |
| `context_purpose` | — |
| `ai_support` | enabled=false; prompts=nenhum; providers=local; fallback=Não aplicável; operações são transacionais e determinísticas |
| `extension_support` | Backups não incluem chrome.storage, IndexedDB, chaves, tokens ou cookies. |
| `dedupe_strategy` | A migração calcula identidades antes da importação e registra duplicatas/rejeições. |
| `snapshot_support` | Tabelas e triggers impedem UPDATE/DELETE de snapshots imutáveis. |
| `tests` | `tests/test_api_data_reliability.py`<br>`tests/test_storage_migrations.py`<br>`tests/test_storage_backup_restore.py`<br>`tests/test_legacy_data_migration.py`<br>`apps/web/tests/e2e/data-reliability.spec.ts` |
| `docs` | `docs/02-architecture/storage-and-history.md`<br>`docs/02-architecture/data-lineage-and-deduplication.md` |
| `status` | `complete` |
| `gaps` | nenhuma registrada |
| `last_verified_commit` | `309f9662f1da410349d85fefdcacff8778cea51e` |

## Como validar

```bash
python scripts/validate_capabilities.py
python scripts/generate_integration_matrix.py --check
```

O modo `--check` não altera arquivos e falha quando a matriz deixa de refletir o manifesto.
