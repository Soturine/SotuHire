# Matriz de capacidades e integração

Esta matriz é gerada a partir de `config/capabilities.json` e confrontada com o OpenAPI real, as rotas TanStack e os arquivos de testes e documentação.

Cada capacidade registra um commit-base ancestral verificável; o manifesto não tenta autorreferenciar o SHA do commit que o contém.

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
| ai_quality_outcomes | Qualidade de IA, feedback humano e resultados profissionais | `/ai-quality` | 10 | dashboard | resume_extraction_v1, job_extraction_multi_domain_v1, domain_classification_v1, profile_items_extractor_v1, profile_lattes_extractor_v1, public_exam_notice_extractor_v1, match_analysis_evidence_based_v1, ats_analysis_v1, resume_tailor_v1, job_wishlist_builder_v1, job_radar_match_explanation_v1, source_import_enrichment_v1, github_repo_analysis_v2, github_profile_analysis_v1, portfolio_gap_analysis_v1, career_advice_v1 | A extensão 0.10.0 envia feedback somente para traces persistidos, sem conteúdo analisado ou segredo. | Traces referenciam execuções e snapshots sem armazenar entradas ou saídas pessoais completas. | complete | Métricas externas dependem de execução opt-in com chaves temporárias. |
| application_lab | Preparar candidatura | `/application-lab` | 9 | match | match_analysis_evidence_based_v1, ats_analysis_v1, resume_tailor_v1 | A extensão 0.10.0 abre o Lab ou o Resume Studio somente com capture_id e job_snapshot_id; o Perfil completo e documentos locais permanecem fora da extensão. | Vincula vaga, mestre, variante, análise, kit e plano à candidatura no Tracker. | complete | Notificações do plano permanecem locais; nenhum calendário externo é criado automaticamente. |
| resume_studio | Resume Studio | `/resume-studio` | 9 | sem contexto dedicado | não | A extensão encaminha a vaga ao Application Lab; não lê nem envia o currículo. | O Tracker preserva snapshots distintos do mestre e da variante usada. | complete | OCR de documentos somente-imagem permanece fora do fluxo padrão e é sinalizado para revisão manual. |
| professional_assets | Professional Assets | `/application-lab` | 5 | sem contexto dedicado | não | A extensão abre o Resume Studio por IDs e nunca lê documentos ou assets locais. | Revisões e dependency_hash preservam o estado usado pelo Application Kit. | complete | Envio por e-mail, calendário externo e submissão automática permanecem fora do produto. |
| opportunity_intelligence | Opportunity Intelligence e Taxonomias | `/radar` | 9 | opportunity_intelligence | opportunity_enrichment_v1, taxonomy_mapping_explanation_v1 | A extensão entrega capturas públicas; não executa ranking nem confirma taxonomia. | Observações imutáveis e rankings versionados no SQLite schema 7. | complete | Datasets oficiais não são baixados implicitamente; stores de Opportunity legados continuam em contrato separado. |
| interview_workflows | Interview, STAR e Follow-up | `/interviews` | 13 | interview | interview_question_generation_v1, interview_answer_drafting_v1, star_story_structuring_v1, follow_up_drafting_v1 | Sem envio de entrevista, resposta ou follow-up pela extensão. | Session guarda IDs dos snapshots de vaga/currículo e evidence_scope_id. | complete | Follow-up permanece rascunho e envio é sempre manual. |
| career_actions | Tarefas, Reminders e Career Plan | `/career` | 8 | career_plan | career_plan_explanation_v1, certification_recommendation_explanation_v1, project_gap_recommendation_v1 | Sem calendário externo, notificações ou execução de tarefa pela extensão. | dependency_hash marca plano stale quando dependências mudam. | complete | ICS é somente download; nenhum calendário é alterado automaticamente. |

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
| `verification_ref` | `capability:resume_extraction` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | A extração isolada não persiste automaticamente uma variante de currículo. |

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
| `verification_ref` | `capability:job_extraction` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | nenhuma registrada |

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
| `verification_ref` | `capability:match` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | nenhuma registrada |

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
| `verification_ref` | `capability:ats` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | nenhuma registrada |

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
| `verification_ref` | `capability:resume_tailor` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Exportação avançada de variantes permanece no roadmap de Resume Studio. |

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
| `verification_ref` | `capability:universal_profile` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Alguns módulos legados ainda mantêm stores próprios e são tratados pela migração gradual. |

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
| `verification_ref` | `capability:public_exams` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | nenhuma registrada |

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
| `verification_ref` | `capability:radar` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Conectores oficiais adicionais permanecem fora desta capacidade atual. |

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
| `verification_ref` | `capability:tracker` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Registros legados sem texto original permanecem sem snapshot inventado. |

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
| `verification_ref` | `capability:github_portfolio` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Análise agregada do perfil GitHub ainda não possui prompt consumido pelo runtime principal.; O relatório de projeto legado ainda não possui snapshot imutável dedicado. |

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
| `verification_ref` | `capability:sources_capture` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | nenhuma registrada |

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
| `verification_ref` | `capability:extension_bridge` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Compatibilidade depende de manter manifesto, extensão e companion versionados em conjunto. |

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
| `verification_ref` | `capability:ai_settings` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | nenhuma registrada |

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
| `verification_ref` | `capability:notifications` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Não existe rota exclusiva; o resumo é exibido no Dashboard e no Radar. |

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
| `verification_ref` | `capability:data_reliability` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | nenhuma registrada |

### Qualidade de IA, feedback humano e resultados profissionais (`ai_quality_outcomes`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `ai_quality_outcomes` |
| `frontend_route` | `/ai-quality` |
| `api_endpoints` | `GET /api/v1/ai/quality/summary`<br>`GET /api/v1/ai/quality/runs`<br>`GET /api/v1/ai/quality/providers`<br>`GET /api/v1/ai/quality/prompts`<br>`GET /api/v1/ai/quality/benchmarks`<br>`POST /api/v1/ai/feedback`<br>`DELETE /api/v1/ai/feedback/{feedback_id}`<br>`GET /api/v1/outcomes/summary`<br>`POST /api/v1/outcomes/events`<br>`GET /api/v1/outcomes/applications/{application_id}` |
| `backend_services` | `apps/api/services/ai_quality.py`<br>`modules/ai/tracing.py`<br>`modules/outcomes/service.py` |
| `core_modules` | `modules/ai/task_registry.py`<br>`modules/ai/evaluation/metrics.py`<br>`modules/ai/feedback.py`<br>`modules/ai/untrusted_content.py` |
| `stores` | `modules/storage/ai_runs.py`<br>`modules/ai/benchmark_store.py`<br>`modules/ai/feedback.py`<br>`modules/outcomes/service.py` |
| `profile_integration` | Usa somente contexto necessário e confirmado; itens não confirmados permanecem sinalizados e não viram fatos. |
| `context_purpose` | `dashboard` |
| `ai_support` | enabled=true; prompts=resume_extraction_v1, job_extraction_multi_domain_v1, domain_classification_v1, profile_items_extractor_v1, profile_lattes_extractor_v1, public_exam_notice_extractor_v1, match_analysis_evidence_based_v1, ats_analysis_v1, resume_tailor_v1, job_wishlist_builder_v1, job_radar_match_explanation_v1, source_import_enrichment_v1, github_repo_analysis_v2, github_profile_analysis_v1, portfolio_gap_analysis_v1, career_advice_v1; providers=local, gemini, openai; fallback=Determinístico local, explícito e mensurado |
| `extension_support` | A extensão 0.10.0 envia feedback somente para traces persistidos, sem conteúdo analisado ou segredo. |
| `dedupe_strategy` | Eventos e feedback usam IDs únicos; métricas de deduplicação são avaliadas separadamente. |
| `snapshot_support` | Traces referenciam execuções e snapshots sem armazenar entradas ou saídas pessoais completas. |
| `tests` | `tests/test_ai_task_registry.py`<br>`tests/test_ai_evaluation_metrics.py`<br>`tests/test_ai_golden_datasets.py`<br>`tests/test_ai_feedback_outcomes.py`<br>`tests/test_ai_quality_api.py`<br>`tests/test_prompt_injection_defense.py` |
| `docs` | `docs/04-ai/ai-evaluation-architecture.md`<br>`docs/04-ai/prompt-governance.md`<br>`docs/02-architecture/outcome-learning.md`<br>`docs/09-testing/ai-benchmarking.md` |
| `status` | `complete` |
| `verification_ref` | `capability:ai_quality_outcomes` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Métricas externas dependem de execução opt-in com chaves temporárias. |

### Preparar candidatura (`application_lab`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `application_lab` |
| `frontend_route` | `/application-lab` |
| `api_endpoints` | `POST /api/v1/application-lab/sessions`<br>`GET /api/v1/application-lab/sessions`<br>`GET /api/v1/application-lab/sessions/{session_id}`<br>`PATCH /api/v1/application-lab/sessions/{session_id}`<br>`POST /api/v1/application-lab/sessions/{session_id}/analyze`<br>`POST /api/v1/application-lab/sessions/{session_id}/variant`<br>`POST /api/v1/application-lab/sessions/{session_id}/kit`<br>`POST /api/v1/application-lab/sessions/{session_id}/action-plan`<br>`POST /api/v1/application-lab/sessions/{session_id}/tracker` |
| `backend_services` | `apps/api/services/application_lab.py` |
| `core_modules` | `modules/application_lab/service.py`<br>`modules/application_lab/readiness.py`<br>`modules/application_lab/repository.py` |
| `stores` | `modules/application_lab/repository.py`<br>`modules/storage/snapshots.py` |
| `profile_integration` | Seleciona referências confirmadas do Perfil e preserva a origem; candidatos não viram fatos automaticamente. |
| `context_purpose` | `match` |
| `ai_support` | enabled=true; prompts=match_analysis_evidence_based_v1, ats_analysis_v1, resume_tailor_v1; providers=local, gemini, openai; fallback=Relatório de prontidão determinístico e fallback local explícito |
| `extension_support` | A extensão 0.10.0 abre o Lab ou o Resume Studio somente com capture_id e job_snapshot_id; o Perfil completo e documentos locais permanecem fora da extensão. |
| `dedupe_strategy` | Reutiliza identidade da captura, job_snapshot_id e snapshots existentes em vez de duplicar a vaga. |
| `snapshot_support` | Vincula vaga, mestre, variante, análise, kit e plano à candidatura no Tracker. |
| `tests` | `tests/test_application_lab_service.py`<br>`tests/test_application_lab_api.py`<br>`tests/test_application_lab_repository.py`<br>`apps/web/tests/e2e/application-lab.spec.ts` |
| `docs` | `docs/02-architecture/application-lab.md`<br>`docs/03-business-rules/application-readiness.md` |
| `status` | `complete` |
| `verification_ref` | `capability:application_lab` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Notificações do plano permanecem locais; nenhum calendário externo é criado automaticamente. |

### Resume Studio (`resume_studio`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `resume_studio` |
| `frontend_route` | `/resume-studio` |
| `api_endpoints` | `POST /api/v1/resume-studio/ingest`<br>`GET /api/v1/resume-studio/master`<br>`PUT /api/v1/resume-studio/master`<br>`GET /api/v1/resume-studio/variants`<br>`POST /api/v1/resume-studio/variants`<br>`GET /api/v1/resume-studio/variants/{variant_id}`<br>`PATCH /api/v1/resume-studio/variants/{variant_id}`<br>`GET /api/v1/resume-studio/templates`<br>`POST /api/v1/resume-studio/variants/{variant_id}/export` |
| `backend_services` | `apps/api/services/application_lab.py` |
| `core_modules` | `modules/application_lab/canonical_document.py`<br>`modules/application_lab/ingestion_service.py`<br>`modules/application_lab/export.py`<br>`modules/parsers/document_ingestion.py` |
| `stores` | `modules/application_lab/repository.py` |
| `profile_integration` | O Currículo Mestre usa itens confirmados e mantém source_profile_item_ids em variantes. |
| `context_purpose` | — |
| `ai_support` | enabled=false; prompts=nenhum; providers=local; fallback=Ingestão, editor, diff, preview e exports PDF/DOCX/JSON Resume determinísticos |
| `extension_support` | A extensão encaminha a vaga ao Application Lab; não lê nem envia o currículo. |
| `dedupe_strategy` | Variantes têm ID próprio, master_resume_id e job_snapshot_id; o mestre nunca é alterado pela variante. |
| `snapshot_support` | O Tracker preserva snapshots distintos do mestre e da variante usada. |
| `tests` | `tests/test_application_lab_api.py`<br>`tests/test_application_lab_service.py`<br>`tests/test_document_ingestion.py` |
| `docs` | `docs/02-architecture/document-ingestion-and-provenance.md`<br>`docs/02-architecture/resume-document-rendering.md` |
| `status` | `complete` |
| `verification_ref` | `capability:resume_studio` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | OCR de documentos somente-imagem permanece fora do fluxo padrão e é sinalizado para revisão manual. |

### Professional Assets (`professional_assets`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `professional_assets` |
| `frontend_route` | `/application-lab` |
| `api_endpoints` | `POST /api/v1/professional-assets`<br>`GET /api/v1/professional-assets`<br>`GET /api/v1/professional-assets/{asset_id}`<br>`PATCH /api/v1/professional-assets/{asset_id}`<br>`POST /api/v1/professional-assets/{asset_id}/status` |
| `backend_services` | `apps/api/services/professional_assets.py` |
| `core_modules` | `modules/professional_assets/models.py`<br>`modules/professional_assets/repository.py` |
| `stores` | `modules/professional_assets/repository.py` |
| `profile_integration` | Assets preservam proveniência e dependem de evidência confirmada antes de uso em candidatura. |
| `context_purpose` | — |
| `ai_support` | enabled=false; prompts=nenhum; providers=local; fallback=CRUD, lifecycle, kit e validação de stale são determinísticos |
| `extension_support` | A extensão abre o Resume Studio por IDs e nunca lê documentos ou assets locais. |
| `dedupe_strategy` | Fingerprint de tipo, conteúdo normalizado e escopo; duplicação explícita cria nova identidade. |
| `snapshot_support` | Revisões e dependency_hash preservam o estado usado pelo Application Kit. |
| `tests` | `tests/test_professional_assets.py`<br>`tests/test_application_lab_service.py` |
| `docs` | `docs/02-architecture/professional-assets.md`<br>`docs/03-business-rules/resume-assets-and-exports.md` |
| `status` | `complete` |
| `verification_ref` | `capability:professional_assets` |
| `verification_base_commit` | `ec87ce6575e8d6ddc3cde9acb520d539cc6b7cef` |
| `verification_date` | `2026-08-03` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Envio por e-mail, calendário externo e submissão automática permanecem fora do produto. |

### Opportunity Intelligence e Taxonomias (`opportunity_intelligence`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `opportunity_intelligence` |
| `frontend_route` | `/radar` |
| `api_endpoints` | `POST /api/v1/opportunities/observations`<br>`GET /api/v1/opportunities/candidates`<br>`POST /api/v1/opportunities/rankings`<br>`GET /api/v1/opportunities/rankings`<br>`POST /api/v1/taxonomy/datasets`<br>`GET /api/v1/taxonomy/datasets`<br>`POST /api/v1/taxonomy/mappings`<br>`GET /api/v1/taxonomy/mappings`<br>`PATCH /api/v1/taxonomy/mappings/{mapping_id}/review` |
| `backend_services` | `apps/api/routes/opportunities.py`<br>`apps/api/routes/taxonomy.py` |
| `core_modules` | `modules/opportunities/intelligence.py`<br>`modules/taxonomy/normalization.py`<br>`modules/storage/career_intelligence.py` |
| `stores` | `modules/storage/career_intelligence.py`<br>`modules/taxonomy/catalog.py` |
| `profile_integration` | Preferências confirmadas alimentam ranking local; mappings não confirmam skills no Perfil. |
| `context_purpose` | `opportunity_intelligence` |
| `ai_support` | enabled=true; prompts=opportunity_enrichment_v1, taxonomy_mapping_explanation_v1; providers=local, gemini, openai; fallback=Dedupe, mapping candidato e ranking determinísticos |
| `extension_support` | A extensão entrega capturas públicas; não executa ranking nem confirma taxonomia. |
| `dedupe_strategy` | Provider/external_id, URL canônica e organização+título+local, preservando proveniência. |
| `snapshot_support` | Observações imutáveis e rankings versionados no SQLite schema 7. |
| `tests` | `tests/test_api_career_intelligence.py`<br>`tests/test_official_opportunity_connectors.py`<br>`tests/test_taxonomy_layer.py` |
| `docs` | `docs/02-architecture/official-opportunity-sources.md`<br>`docs/02-architecture/taxonomy-layer.md`<br>`docs/03-business-rules/opportunity-deduplication.md` |
| `status` | `complete` |
| `verification_ref` | `capability:opportunity_intelligence` |
| `verification_base_commit` | `c7aca1aba9fcd9eba858b5416316a380abb5f2d0` |
| `verification_date` | `2026-08-10` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Datasets oficiais não são baixados implicitamente; stores de Opportunity legados continuam em contrato separado. |

### Interview, STAR e Follow-up (`interview_workflows`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `interview_workflows` |
| `frontend_route` | `/interviews` |
| `api_endpoints` | `GET /api/v1/interviews`<br>`POST /api/v1/interviews`<br>`GET /api/v1/interviews/{session_id}/preparation`<br>`POST /api/v1/interviews/{session_id}/prepare`<br>`GET /api/v1/interviews/star-stories`<br>`POST /api/v1/interviews/star-stories`<br>`GET /api/v1/interviews/questions`<br>`POST /api/v1/interviews/questions`<br>`GET /api/v1/interviews/answers`<br>`POST /api/v1/interviews/answers`<br>`GET /api/v1/interviews/follow-ups`<br>`POST /api/v1/interviews/follow-ups`<br>`POST /api/v1/interviews/ai/{task_id}` |
| `backend_services` | `apps/api/routes/interviews.py` |
| `core_modules` | `modules/interviews/models.py`<br>`modules/interviews/preparation.py`<br>`modules/ai/career_workflows.py` |
| `stores` | `modules/storage/career_workflows.py` |
| `profile_integration` | Preparação e drafts usam somente evidências confirmadas e source refs. |
| `context_purpose` | `interview` |
| `ai_support` | enabled=true; prompts=interview_question_generation_v1, interview_answer_drafting_v1, star_story_structuring_v1, follow_up_drafting_v1; providers=local, gemini, openai; fallback=Preparação local e drafts conservadores revisáveis |
| `extension_support` | Sem envio de entrevista, resposta ou follow-up pela extensão. |
| `dedupe_strategy` | IDs estáveis e vínculos SQLite; preparação é única por session_id. |
| `snapshot_support` | Session guarda IDs dos snapshots de vaga/currículo e evidence_scope_id. |
| `tests` | `tests/test_interview_and_career_workflows.py`<br>`tests/test_api_interview_career.py`<br>`tests/test_ai_career_workflow_tasks.py` |
| `docs` | `docs/02-architecture/interview-and-career-workflows.md`<br>`docs/03-business-rules/interview-star-follow-up.md` |
| `status` | `complete` |
| `verification_ref` | `capability:interview_workflows` |
| `verification_base_commit` | `c7aca1aba9fcd9eba858b5416316a380abb5f2d0` |
| `verification_date` | `2026-08-10` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | Follow-up permanece rascunho e envio é sempre manual. |

### Tarefas, Reminders e Career Plan (`career_actions`)

| Campo | Valor verificado |
|---|---|
| `capability_id` | `career_actions` |
| `frontend_route` | `/career` |
| `api_endpoints` | `GET /api/v1/career/tasks`<br>`POST /api/v1/career/tasks`<br>`GET /api/v1/career/reminders`<br>`POST /api/v1/career/reminders`<br>`GET /api/v1/career/plans`<br>`POST /api/v1/career/plans`<br>`POST /api/v1/career/calendar/export`<br>`POST /api/v1/career/ai/{task_id}` |
| `backend_services` | `apps/api/routes/career.py` |
| `core_modules` | `modules/career_actions/models.py`<br>`modules/career_actions/ics.py`<br>`modules/ai/career_workflows.py` |
| `stores` | `modules/storage/career_workflows.py` |
| `profile_integration` | Planos citam perfil/evidências sem promover recomendações a fatos. |
| `context_purpose` | `career_plan` |
| `ai_support` | enabled=true; prompts=career_plan_explanation_v1, certification_recommendation_explanation_v1, project_gap_recommendation_v1; providers=local, gemini, openai; fallback=Tarefas, plano e ICS locais |
| `extension_support` | Sem calendário externo, notificações ou execução de tarefa pela extensão. |
| `dedupe_strategy` | IDs próprios e upsert transacional no SQLite schema 7. |
| `snapshot_support` | dependency_hash marca plano stale quando dependências mudam. |
| `tests` | `tests/test_interview_and_career_workflows.py`<br>`tests/test_api_interview_career.py` |
| `docs` | `docs/02-architecture/interview-and-career-workflows.md`<br>`docs/03-business-rules/career-actions.md` |
| `status` | `complete` |
| `verification_ref` | `capability:career_actions` |
| `verification_base_commit` | `c7aca1aba9fcd9eba858b5416316a380abb5f2d0` |
| `verification_date` | `2026-08-10` |
| `verification_command` | `python scripts/validate_capabilities.py` |
| `known_gaps` | ICS é somente download; nenhum calendário é alterado automaticamente. |

## Como validar

```bash
python scripts/validate_capabilities.py
python scripts/generate_integration_matrix.py --check
```

O modo `--check` não altera arquivos e falha quando a matriz deixa de refletir o manifesto.
