# Triagem de código morto, duplicação e legado — 2026-11

Parte da [auditoria independente de 2026-11](2026-11-independent-assurance-audit.md). Fonte dos
candidatos: `derivanta-engine inspect --maintainability` sobre `main` `8ea37d7` (relatório bruto
fora do repositório; SHA-256 em [dogfood](2026-11-dogfood-and-external-research.md)). Um candidato
é uma hipótese: só vira remoção ou consolidação depois de checar imports, referências por string,
`__all__`, testes, docs, CLI/scripts e contratos públicos.

## Resultado

Os 170 candidatos de duplicação (152 `DUPLICATE_TABLE` + 18 `DUPLICATE_BODY`) e os 36
`UNREFERENCED_DEFINITION` têm decisão individual no apêndice. Os 65 `HIGH_COMPLEXITY` não foram
triados neste ciclo (`NOT_RUN`).

| Sinal | Decisão | Qtde |
| --- | --- | --- |
| DUPLICATE_BODY | CONSOLIDATED | 3 |
| DUPLICATE_BODY | KEEP | 9 |
| DUPLICATE_BODY | REMOVED | 6 |
| DUPLICATE_TABLE | CONSOLIDATED | 26 |
| DUPLICATE_TABLE | DEFER | 10 |
| DUPLICATE_TABLE | KEEP | 109 |
| DUPLICATE_TABLE | KEEP_PINNED | 5 |
| DUPLICATE_TABLE | REMOVED | 2 |
| UNREFERENCED_DEFINITION | REMOVED | 36 |

Regras usadas para `KEEP` (cada linha do apêndice diz qual):

- **oráculo de teste**: uma tabela repetida em `tests/` é a expectativa independente; importar a
  tabela de produção tornaria o teste tautológico.
- **`__all__`/reexport**: lista de exportação de pacote repetindo nomes do módulo. Falso positivo do
  sinal (registrado como lacuna do Engine no doc de dogfood).
- **sobreposição parcial**: a tabela repete só parte de outra (ex.: 4 de 15 tipos de evidência);
  são vocabulários com contratos diferentes.
- **UI legada**: `modules/ui` (Streamlit) está congelada atrás do extra `legacy-ui`.

`CONSOLIDATED` quer dizer que o conceito ganhou um dono e os outros lugares importam ou derivam
dele; `tests/test_shared_vocabularies.py`, `tests/test_security_secret_fields.py` e
`tests/test_evidence_review_reconciliation.py` falham se uma cópia voltar ou divergir.
`KEEP_PINNED`: importância/criticidade de requisito ficam em `modules/ai/schemas` e em
`modules/matching/models` porque `matching.models` importar `modules.ai` causa `ImportError`
(o `__init__` de `modules.ai` carrega providers → analyzer → `matching.models`); o teste fixa a
igualdade.

## Além do Engine: grafo de imports a partir dos entrypoints reais

O sinal do Engine é por definição; ele não vê um módulo inteiro cujas funções se chamam entre si
mas que ninguém importa. Um grafo AST de imports (incluindo strings `modules.*` usadas por
importlib/uvicorn e pacotes-pai) a partir de `apps/api/main.py`, rotas, `modules/local_api`,
`app.py` e `scripts/` apontou, depois das remoções:

| Módulo | Alcance | Decisão |
| --- | --- | --- |
| `modules/ai/claim_validation.py` | só testes | **Achado SH-NEW-014**: a validação de afirmações proibidas/sem evidência não roda em produção, embora o teste se chame `..._runs_after_schema`. Tratado no próximo CP. |
| `modules/ai/guidance.py`, `modules/ai/provider.py`, `modules/rag/*`, `modules/sources/base.py`, `modules/search_intelligence/source_ranker.py`, `modules/memory/memory_index.py`, `modules/matching/exceptions.py` | inalcançável | `DEFER`: sem importador de produção nem de teste; remover no próximo CP após checar docs que os citam |
| `modules/core/schemas.py`, `modules/portfolio/portfolio_score.py`, `modules/search_intelligence/post_detector.py`, `modules/search_intelligence/query_generator.py` | só testes | `DEFER`: decidir entre ligar ao produto ou remover junto com os testes |

## Outros achados desta triagem

- `streamlit` e `pandas` eram dependências obrigatórias; `pandas` não tinha nenhum import e o
  Streamlit só serve a UI legada. Viraram extra (`legacy-ui`); fechamento de runtime 51 → 28.
- `docs/requirements/*.txt` duplicava o `pyproject.toml` e já divergia dele (piso de `pypdf` abaixo
  do corrigido). Removido; guias e mensagens de instalação apontam para os extras.
- A checagem de campos de credencial tinha quatro cópias, duas sem `headers`.
- `docs/04-ai/ai-cost-latency.md` descrevia métricas que o painel nunca calculou.
- `config/capabilities.json` declarava como store da capacidade `data_reliability` um arquivo do
  repositório genérico sem consumidor.


## Apêndice — decisão por candidato

| Sinal | Candidato | Par/dono | Decisão | Motivo |
| --- | --- | --- | --- | --- |
| DUPLICATE_BODY | `apps/api/routes/profile.py:83 `import_lattes_profile` | `apps/api/routes/profile.py::draft_lattes_profile` | CONSOLIDATED | uma função para as duas rotas; `import-lattes` deprecated (38ec405) |
| UNREFERENCED_DEFINITION | `apps/api/schemas/settings.py:153 `default_model_for_provider` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `apps/api/services/ai_settings.py:515` | `apps/api/schemas/settings.py:13` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| UNREFERENCED_DEFINITION | `apps/api/services/ai_settings.py:645 `validate_safe_response` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `apps/api/services/extension.py:131` | `apps/api/services/extension.py:69` | CONSOLIDATED | `ENABLED_EXTENSION_FLOWS` (caf26ac) |
| DUPLICATE_TABLE | `apps/api/services/public_exams.py:147` | `apps/api/services/profile.py:280` | CONSOLIDATED | `modules/security/credentials.contains_secret_field` (4000993) |
| DUPLICATE_TABLE | `apps/api/services/radar.py:642` | `apps/api/services/profile.py:280` | CONSOLIDATED | `modules/security/credentials.contains_secret_field` (4000993) |
| DUPLICATE_BODY | `apps/api/services/sources.py:538 `_contains_secret_field` | `apps/api/services/public_exams.py::_contains_secret_field` | CONSOLIDATED | `modules/security/credentials.contains_secret_field` (4000993) |
| DUPLICATE_TABLE | `apps/api/services/sources.py:539` | `apps/api/services/profile.py:280` | CONSOLIDATED | `modules/security/credentials.contains_secret_field` (4000993) |
| DUPLICATE_TABLE | `modules/ai/career_workflows.py:28` | `apps/api/routes/career.py:123` | KEEP | sobreposição parcial (5 de 5/9 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:270 `cost_per_accepted_suggestion` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:81 `date_accuracy` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:99 `domain_classification_accuracy` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:274 `quality_per_cost` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:278 `quality_per_latency` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:95 `requirement_classification_accuracy` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:87 `salary_accuracy` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:133 `source_ref_coverage` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:45 `type_correctness` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/ai/evaluation/metrics.py:143 `unconfirmed_claim_rate` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_BODY | `modules/ai/model_catalog.py:305 `_read_json` | `apps/api/services/ai_settings.py::AiSettingsStore._read_json` | KEEP | helper de 3–7 linhas em módulos sem relação; acoplar custaria mais que a duplicação |
| DUPLICATE_TABLE | `modules/ai/providers/gemini_provider.py:348` | `apps/api/schemas/analysis.py:238` | CONSOLIDATED | `modules/schemas/job_analysis.Recommendation` (caf26ac) |
| DUPLICATE_TABLE | `modules/ai/providers/gemini_provider.py:502` | `modules/ai/providers/gemini_provider.py:487` | KEEP | sobreposição parcial (4 de 5/11 strings): vocabulário com contrato próprio |
| DUPLICATE_BODY | `modules/ai/providers/openai_provider.py:386 `_integer` | `modules/ai/providers/gemini_provider.py::_integer` | KEEP | helper de 3–7 linhas em módulos sem relação; acoplar custaria mais que a duplicação |
| DUPLICATE_TABLE | `modules/ai/providers/openai_provider.py:431` | `modules/ai/providers/gemini_provider.py:487` | KEEP | sobreposição parcial (4 de 5/8 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/ai/providers/openai_provider.py:416` | `modules/ai/providers/gemini_provider.py:487` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/ai/schemas/resume_extraction.py:114` | `modules/ai/schemas/job_extraction.py:18` | KEEP | sobreposição parcial (11 de 17/12 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/ai/schemas/resume_extraction.py:44` | `modules/ai/schemas/job_extraction.py:89` | KEEP | sobreposição parcial (10 de 11/10 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/ai/structured_job_extractor.py:34` | `modules/ai/schemas/job_extraction.py:60` | CONSOLIDATED | vocabulários do schema `job_extraction` + `get_args` (CP-03) |
| DUPLICATE_TABLE | `modules/ai/structured_job_extractor.py:45` | `modules/ai/schemas/job_extraction.py:89` | CONSOLIDATED | vocabulários do schema `job_extraction` + `get_args` (CP-03) |
| DUPLICATE_TABLE | `modules/ai/structured_job_extractor.py:287` | `modules/ai/schemas/job_extraction.py:37` | CONSOLIDATED | vocabulários do schema `job_extraction` + `get_args` (CP-03) |
| DUPLICATE_TABLE | `modules/ai/structured_job_extractor.py:261` | `modules/ai/schemas/job_extraction.py:18` | CONSOLIDATED | vocabulários do schema `job_extraction` + `get_args` (CP-03) |
| DUPLICATE_TABLE | `modules/ai/structured_job_extractor.py:32` | `modules/ai/schemas/job_extraction.py:58` | CONSOLIDATED | vocabulários do schema `job_extraction` + `get_args` (CP-03) |
| DUPLICATE_TABLE | `modules/ai/structured_resume_extractor.py:37` | `modules/ai/schemas/job_extraction.py:18` | KEEP | sobreposição parcial (11 de 17/12 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/ai/structured_resume_extractor.py:272` | `modules/ai/schemas/job_extraction.py:18` | KEEP | sobreposição parcial (11 de 17/12 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/ai/structured_resume_extractor.py:51` | `modules/ai/schemas/job_extraction.py:89` | KEEP | sobreposição parcial (10 de 11/10 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/alerts/notifier.py:6 `should_alert` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/analyzer/recommendation.py:10` | `apps/api/schemas/analysis.py:238` | CONSOLIDATED | `modules/schemas/job_analysis.Recommendation` (caf26ac) |
| DUPLICATE_TABLE | `modules/application_lab/models.py:99` | `modules/application_lab/ingestion_service.py:59` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/application_lab/models.py:350` | `modules/application_lab/__init__.py:17` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_TABLE | `modules/application_lab/readiness.py:354` | `modules/application_lab/models.py:196` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/application_lab/service.py:964` | `modules/application_lab/readiness.py:304` | KEEP | sobreposição parcial (4 de 5/4 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/application_lab/service.py:50` | `apps/api/schemas/application_lab.py:111` | KEEP | sobreposição parcial (4 de 5/4 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/application_lab/service.py:962 `_job_requirements` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/career_actions/models.py:80` | `modules/ai/schemas/career_workflows.py:61` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/career_actions/models.py:33` | `modules/application_lab/models.py:335` | KEEP | sobreposição parcial (4 de 4/5 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/career_actions/models.py:117` | `modules/career_actions/__init__.py:14` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_TABLE | `modules/context/engine.py:332` | `apps/api/services/extension.py:736` | KEEP | sobreposição parcial (4 de 4/5 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/context/engine.py:313` | `modules/context/engine.py:280` | KEEP | sobreposição parcial (5 de 15/11 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/context/formatters.py:341` | `modules/context/engine.py:280` | KEEP | sobreposição parcial (8 de 15/16 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/context/formatters.py:184` | `modules/context/engine.py:280` | KEEP | sobreposição parcial (5 de 15/11 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/copilot_v2/models.py:156 `ProfessionalRegistration` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/core/schemas.py:70 `AnalysisReport` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/core/text_utils.py:9` | `modules/core/opportunity_identity.py:11` | KEEP | sobreposição parcial (8 de 9/32 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/domain_intelligence/domain_catalog.py:49` | `modules/application_lab/readiness.py:69` | KEEP | sobreposição parcial (7 de 14/12 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/domain_intelligence/domain_catalog.py:17` | `apps/api/routes/career_intelligence.py:15` | CONSOLIDATED | `DOMAINS = get_args(CareerDomain)` (caf26ac) |
| UNREFERENCED_DEFINITION | `modules/github_analyzer/exceptions.py:18 `GitHubAnalysisUnavailable` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/github_analyzer/repository_models.py:116` | `apps/api/schemas/analysis.py:187` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/github_analyzer/schemas.py:132` | `modules/github_analyzer/schemas.py:13` | KEEP | sobreposição parcial (4 de 5/4 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/github_analyzer/tree_builder.py:16` | `modules/github_analyzer/file_sampler.py:18` | KEEP | sobreposição parcial (8 de 14/10 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/github_analyzer/tree_builder.py:28` | `modules/github_analyzer/file_filters.py:24` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/interviews/models.py:166` | `modules/interviews/__init__.py:15` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_TABLE | `modules/interviews/models.py:98` | `modules/interviews/models.py:80` | KEEP | sobreposição parcial (4 de 4/5 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/local_api/app.py:229` | `apps/api/services/extension.py:69` | CONSOLIDATED | `ENABLED_EXTENSION_FLOWS` (caf26ac) |
| UNREFERENCED_DEFINITION | `modules/local_api/security.py:37 `safe_log_label` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/local_api/security.py:25 `token_is_valid` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/matching/domain_weights.py:296` | `apps/api/routes/career_intelligence.py:15` | CONSOLIDATED | `DOMAINS = get_args(CareerDomain)` (caf26ac) |
| DUPLICATE_TABLE | `modules/matching/domain_weights.py:240` | `apps/api/routes/career_intelligence.py:15` | CONSOLIDATED | `DOMAINS = get_args(CareerDomain)` (caf26ac) |
| DUPLICATE_TABLE | `modules/matching/domain_weights.py:46` | `apps/api/routes/career_intelligence.py:15` | CONSOLIDATED | `DOMAINS = get_args(CareerDomain)` (caf26ac) |
| UNREFERENCED_DEFINITION | `modules/matching/exceptions.py:10 `MatchInputError` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/matching/models.py:40` | `modules/ai/schemas/job_extraction.py:37` | KEEP_PINNED | import cíclico via `modules/ai/__init__`; igualdade fixada em `tests/test_shared_vocabularies.py` |
| DUPLICATE_TABLE | `modules/matching/models.py:38` | `modules/ai/schemas/job_extraction.py:37` | KEEP_PINNED | import cíclico via `modules/ai/__init__`; igualdade fixada em `tests/test_shared_vocabularies.py` |
| DUPLICATE_TABLE | `modules/matching/models.py:39` | `modules/application_lab/models.py:196` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/matching/models.py:43` | `apps/api/schemas/analysis.py:238` | CONSOLIDATED | `modules/schemas/job_analysis.Recommendation` (caf26ac) |
| DUPLICATE_TABLE | `modules/matching/models.py:37` | `modules/ai/schemas/job_extraction.py:36` | KEEP_PINNED | import cíclico via `modules/ai/__init__`; igualdade fixada em `tests/test_shared_vocabularies.py` |
| DUPLICATE_TABLE | `modules/matching/models.py:55` | `modules/ai/schemas/common.py:53` | KEEP | sobreposição parcial (4 de 6/4 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/matching/models.py:17` | `modules/ai/schemas/job_extraction.py:18` | KEEP | sobreposição parcial (17 de 17/19 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/matching/requirement_matcher.py:379` | `modules/ai/schemas/job_extraction.py:37` | KEEP_PINNED | import cíclico via `modules/ai/__init__`; igualdade fixada em `tests/test_shared_vocabularies.py` |
| DUPLICATE_TABLE | `modules/matching/requirement_matcher.py:340` | `modules/ai/schemas/job_extraction.py:36` | KEEP_PINNED | import cíclico via `modules/ai/__init__`; igualdade fixada em `tests/test_shared_vocabularies.py` |
| UNREFERENCED_DEFINITION | `modules/memory/memory_index.py:22 `matches_filters` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/memory/schemas.py:12` | `modules/context/engine.py:280` | KEEP | sobreposição parcial (8 de 15/16 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/opportunities/intelligence.py:344` | `modules/opportunities/__init__.py:16` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_TABLE | `modules/parsers/document_ingestion.py:139` | `modules/parsers/document_ingestion.py:19` | KEEP | sobreposição parcial (5 de 5/6 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/parsers/document_ingestion.py:345` | `modules/parsers/document_ingestion.py:334` | CONSOLIDATED | `_ACTIVE_TAGS` (CP-03) |
| DUPLICATE_TABLE | `modules/parsers/job_description_parser.py:10` | `modules/github_analyzer/analyzer_service.py:701` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_TABLE | `modules/parsers/resume_parser.py:171` | `modules/parsers/resume_parser.py:92` | KEEP | sobreposição parcial (4 de 8/16 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/parsers/resume_parser.py:106` | `modules/parsers/job_description_parser.py:82` | KEEP | sobreposição parcial (7 de 10/14 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/portfolio/analyzer.py:166` | `modules/github_analyzer/schemas.py:12` | CONSOLIDATED | `modules/portfolio/schemas.Grade` (caf26ac) |
| DUPLICATE_TABLE | `modules/portfolio/analyzer.py:178` | `modules/github_analyzer/schemas.py:12` | CONSOLIDATED | `modules/portfolio/schemas.Grade` (caf26ac) |
| DUPLICATE_TABLE | `modules/portfolio/file_sampler.py:19` | `modules/github_analyzer/file_filters.py:9` | KEEP | sobreposição parcial (8 de 12/8 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/portfolio/file_sampler.py:18` | `modules/github_analyzer/file_sampler.py:52` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/portfolio/file_sampler.py:5` | `modules/github_analyzer/file_sampler.py:18` | KEEP | sobreposição parcial (8 de 14/11 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/portfolio/file_sampler.py:29` | `modules/github_analyzer/file_filters.py:32` | KEEP | sobreposição parcial (18 de 25/19 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/portfolio/schemas.py:11` | `modules/context/formatters.py:341` | KEEP | sobreposição parcial (4 de 16/4 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/portfolio/schemas.py:67` | `modules/github_analyzer/schemas.py:12` | CONSOLIDATED | `modules/portfolio/schemas.Grade` (caf26ac) |
| DUPLICATE_TABLE | `modules/profile/extraction.py:60` | `modules/profile/extraction.py:15` | KEEP | sobreposição parcial (4 de 9/8 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/profile/extraction.py:235` | `modules/profile/extraction.py:15` | KEEP | sobreposição parcial (6 de 9/19 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/profile/extraction.py:22` | `modules/application_lab/readiness.py:69` | KEEP | sobreposição parcial (5 de 14/7 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/profile/lattes_parser.py:6 `extract_lattes_keywords` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/profile/linkedin_export_parser.py:8 `discover_linkedin_csv_files` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_BODY | `modules/profile/models.py:51 `ProfileItem.normalize_review_status` | `modules/profile/context.py::ProfileContextItem.normalize_review_status` | CONSOLIDATED | `modules/evidence.reconcile_review_status` (81b748a) |
| DUPLICATE_TABLE | `modules/profile/orchestrator.py:140` | `modules/academic/lattes_parser.py:384` | KEEP | sobreposição parcial (8 de 8/11 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/profile/orchestrator.py:21` | `modules/academic/lattes_parser.py:384` | KEEP | sobreposição parcial (6 de 8/47 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/profile/orchestrator.py:174` | `modules/context/engine.py:280` | KEEP | sobreposição parcial (4 de 15/10 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/profile/orchestrator.py:156` | `modules/profile/json_resume.py:17` | KEEP | sobreposição parcial (7 de 8/12 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/profile/profile_builder.py:13` | `modules/context/engine.py:363` | KEEP | sobreposição parcial (5 de 6/6 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/profile/profile_builder.py:15` | `modules/ai/schemas/job_extraction.py:60` | KEEP | sobreposição parcial (4 de 9/6 strings): vocabulário com contrato próprio |
| DUPLICATE_BODY | `modules/profile/service.py:170 `_unique` | `modules/profile/extraction.py::_unique` | KEEP | helper de 3–7 linhas em módulos sem relação; acoplar custaria mais que a duplicação |
| UNREFERENCED_DEFINITION | `modules/public_exams/formatters.py:10 `notice_context_evidence` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/public_exams/models.py:13` | `modules/ai/schemas/job_extraction.py:18` | KEEP | sobreposição parcial (6 de 17/17 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/public_exams/parser.py:472` | `modules/profile/extraction.py:41` | KEEP | sobreposição parcial (6 de 15/7 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/public_exams/parser.py:244` | `modules/parsers/resume_parser.py:106` | KEEP | sobreposição parcial (4 de 14/8 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/public_exams/scoring.py:135` | `modules/public_exams/models.py:13` | KEEP | sobreposição parcial (5 de 17/5 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/public_exams/scoring.py:167` | `modules/profile/extraction.py:41` | KEEP | sobreposição parcial (10 de 15/10 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/public_exams/scoring.py:201` | `modules/profile/extraction.py:41` | KEEP | sobreposição parcial (6 de 15/6 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/models.py:31` | `modules/radar/models.py:18` | KEEP | sobreposição parcial (5 de 11/6 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/service.py:520` | `modules/radar/models.py:39` | KEEP | sobreposição parcial (4 de 7/4 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:377` | `modules/profile/orchestrator.py:193` | KEEP | sobreposição parcial (4 de 5/5 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:38` | `modules/profile/extraction.py:12` | KEEP | sobreposição parcial (6 de 7/7 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:104` | `modules/profile/extraction.py:20` | KEEP | sobreposição parcial (5 de 6/7 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:44` | `modules/profile/extraction.py:15` | KEEP | sobreposição parcial (8 de 9/14 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:18` | `modules/domain_intelligence/domain_catalog.py:132` | KEEP | sobreposição parcial (4 de 6/13 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:71` | `modules/profile/extraction.py:18` | KEEP | sobreposição parcial (5 de 7/6 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:92` | `modules/application_lab/readiness.py:69` | KEEP | sobreposição parcial (6 de 14/8 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:98` | `modules/profile/extraction.py:21` | KEEP | sobreposição parcial (4 de 5/6 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:77` | `modules/context/formatters.py:222` | KEEP | sobreposição parcial (4 de 19/8 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:94` | `modules/parsers/job_description_parser.py:10` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_TABLE | `modules/radar/wishlist_draft.py:65` | `modules/profile/extraction.py:17` | KEEP | sobreposição parcial (6 de 7/7 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/resume_tailor/keyword_injector.py:8 `suggest_supported_keywords` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/resume_tailor/section_ranker.py:29 `rank_sections` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/schemas/job_analysis.py:9` | `apps/api/schemas/analysis.py:238` | CONSOLIDATED | `modules/schemas/job_analysis.Recommendation` (caf26ac) |
| DUPLICATE_TABLE | `modules/schemas/job_posting.py:9` | `modules/ai/schemas/job_extraction.py:58` | KEEP | sobreposição parcial (4 de 5/4 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/scraping/connectors/job_posting.py:63` | `modules/scraping/connectors/job_posting.py:57` | KEEP | sobreposição parcial (6 de 7/6 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/search_intelligence/source_ranker.py:64 `rank_sources` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/search_intelligence/source_registry.py:13 `find_source` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/security/local_auth.py:280` | `modules/security/__init__.py:16` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_BODY | `modules/sources/imports.py:256 `SourceImportStore.save` | `modules/public_exams/store.py::PublicExamStore.save_state` | KEEP | gravação JSON de stores distintos com donos e arquivos próprios |
| DUPLICATE_TABLE | `modules/sources/imports.py:28` | `modules/core/collection_method.py:6` | KEEP | sobreposição parcial (7 de 14/10 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/sources/imports.py:41` | `modules/radar/models.py:48` | KEEP | sobreposição parcial (6 de 8/8 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/sources/registry.py:15 `get_connector` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/sources/registry.py:20 `list_connectors` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/sources/registry.py:10 `register_connector` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/storage/ai_runs.py:380` | `apps/api/config.py:84` | DEFER | lista igual em dois donos; candidata a `get_args`/constante única no próximo ciclo |
| DUPLICATE_TABLE | `modules/storage/backup.py:35` | `apps/api/services/profile.py:280` | CONSOLIDATED | `modules/security/credentials.contains_secret_field` (4000993) |
| UNREFERENCED_DEFINITION | `modules/storage/database.py:74 `database_path_for` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/storage/legacy_migration.py:414` | `modules/interviews/models.py:98` | KEEP | sobreposição parcial (4 de 5/5 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/storage/legacy_migration.py:24` | `modules/storage/health.py:75` | CONSOLIDATED | `legacy_migration.LEGACY_PATHS` usado pelo health (CP-03) |
| DUPLICATE_TABLE | `modules/storage/migrations/runner.py:163` | `modules/storage/migrations/__init__.py:7` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_TABLE | `modules/taxonomy/models.py:96` | `modules/taxonomy/__init__.py:15` | KEEP | lista `__all__`/reexport de pacote: falso positivo do sinal |
| DUPLICATE_TABLE | `modules/tracker/career_analytics.py:203` | `modules/application_lab/readiness.py:69` | KEEP | sobreposição parcial (4 de 14/6 strings): vocabulário com contrato próprio |
| DUPLICATE_TABLE | `modules/tracker/career_analytics.py:174` | `modules/tracker/career_analytics.py:137` | KEEP | sobreposição parcial (5 de 7/5 strings): vocabulário com contrato próprio |
| UNREFERENCED_DEFINITION | `modules/tracker/follow_up.py:8 `next_follow_up` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `modules/tracker/kanban.py:10 `is_valid_status` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `modules/ui/layout.py:32` | `modules/profile/profile_builder.py:15` | KEEP | UI Streamlit legada congelada (extra `legacy-ui`) |
| DUPLICATE_TABLE | `modules/ui/layout.py:33` | `modules/context/engine.py:363` | KEEP | UI Streamlit legada congelada (extra `legacy-ui`) |
| DUPLICATE_TABLE | `modules/ui/pages.py:821` | `apps/api/schemas/analysis.py:238` | CONSOLIDATED | `modules/schemas/job_analysis.Recommendation` (caf26ac) |
| DUPLICATE_TABLE | `modules/ui/project_page.py:70` | `modules/context/formatters.py:341` | KEEP | UI Streamlit legada congelada (extra `legacy-ui`) |
| DUPLICATE_TABLE | `modules/ui/quick_mode.py:11` | `modules/ui/advanced_mode.py:5` | KEEP | UI Streamlit legada congelada (extra `legacy-ui`) |
| DUPLICATE_TABLE | `scripts/capture_screenshots.py:141` | `modules/parsers/job_description_parser.py:10` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/capture_screenshots.py:147` | `modules/parsers/job_description_parser.py:10` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_BODY | `scripts/capture_streamlit_v1_1_screenshots.py:67 `main` | `scripts/capture_screenshots.py::main` | REMOVED | script de versão passada removido (b6f2160) |
| DUPLICATE_BODY | `scripts/capture_v1110_walkthrough.py:76 `_save` | `scripts/capture_v1101_walkthrough.py::_save` | REMOVED | script de versão passada removido (b6f2160) |
| DUPLICATE_BODY | `scripts/capture_v1110_walkthrough.py:67 `_shot` | `scripts/capture_v1101_walkthrough.py::_shot` | REMOVED | script de versão passada removido (b6f2160) |
| DUPLICATE_BODY | `scripts/capture_v1110_walkthrough.py:108 `_start_server` | `scripts/capture_v1101_walkthrough.py::_start_server` | REMOVED | script de versão passada removido (b6f2160) |
| DUPLICATE_BODY | `scripts/capture_v1110_walkthrough.py:130 `_wait` | `scripts/capture_v1101_walkthrough.py::_wait` | REMOVED | script de versão passada removido (b6f2160) |
| DUPLICATE_BODY | `scripts/capture_v1110_walkthrough.py:25 `main` | `scripts/capture_v1101_walkthrough.py::main` | REMOVED | script de versão passada removido (b6f2160) |
| DUPLICATE_TABLE | `scripts/capture_v1110_walkthrough.py:114` | `scripts/capture_v1101_walkthrough.py:120` | REMOVED | arquivo removido nesta auditoria |
| DUPLICATE_TABLE | `scripts/capture_v1110_walkthrough.py:142` | `scripts/capture_v1101_walkthrough.py:148` | REMOVED | arquivo removido nesta auditoria |
| DUPLICATE_TABLE | `scripts/capture_v2_walkthrough.py:144` | `scripts/capture_v1101_walkthrough.py:120` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/capture_v2_walkthrough.py:172` | `scripts/capture_v1101_walkthrough.py:148` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/capture_web_walkthrough.py:180` | `scripts/capture_v1101_walkthrough.py:120` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/capture_web_walkthrough.py:200` | `scripts/capture_v1101_walkthrough.py:148` | KEEP | constante local de script de desenvolvimento |
| UNREFERENCED_DEFINITION | `scripts/generate_prompt_catalog.py:219 `_consumer_references` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| UNREFERENCED_DEFINITION | `scripts/generate_prompt_catalog.py:233 `_references` | `—` | REMOVED | sem consumidor (00f8a98 / 9f9ce28) |
| DUPLICATE_TABLE | `scripts/package_extension.py:74` | `modules/github_analyzer/file_filters.py:32` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_BODY | `scripts/run_ai_benchmark.py:656 `_int_or_none` | `modules/ai/providers/gemini_provider.py::_integer` | KEEP | helper de 3–7 linhas em módulos sem relação; acoplar custaria mais que a duplicação |
| DUPLICATE_TABLE | `scripts/run_ai_benchmark.py:543` | `modules/ai/providers/gemini_provider.py:487` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/run_ai_benchmark.py:172` | `scripts/run_ai_benchmark.py:122` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/scan_secrets.py:19` | `modules/github_analyzer/file_filters.py:9` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/validate_capabilities.py:231` | `scripts/validate_capabilities.py:17` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/validate_capabilities.py:146` | `scripts/validate_capabilities.py:17` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `scripts/validate_capabilities.py:61` | `apps/api/main.py:59` | KEEP | constante local de script de desenvolvimento |
| DUPLICATE_TABLE | `tests/test_advanced_mode_layout.py:5` | `modules/ui/advanced_mode.py:5` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_ai_career_workflow_tasks.py:8` | `apps/api/routes/career.py:123` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_ai_golden_datasets.py:4` | `apps/api/services/ai_settings.py:37` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_BODY | `tests/test_api_radar_scheduler.py:37 `_patch_scraping_fetch` | `tests/test_api_radar.py::_patch_scraping_fetch` | KEEP | helper de teste local; testes independentes entre si |
| DUPLICATE_BODY | `tests/test_application_lab_service.py:26 `EmptyContextEngine.build` | `tests/test_application_lab_api.py::EmptyContextEngine.build` | KEEP | helper de teste local; testes independentes entre si |
| DUPLICATE_TABLE | `tests/test_browser_extension_manifest.py:10` | `scripts/package_extension.py:33` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_capability_documentation_generators.py:57` | `scripts/validate_capabilities.py:17` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_domain_matching_policies.py:6` | `apps/api/routes/career_intelligence.py:15` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_extension_ai_report_schema.py:22` | `modules/github_analyzer/schemas.py:12` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_extension_permissions_minimal.py:9` | `scripts/package_extension.py:33` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_extension_repo_sampling.py:6` | `scripts/capture_screenshots.py:168` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_BODY | `tests/test_github_tree_builder.py:8 `_tree` | `tests/test_github_file_sampler.py::_tree` | KEEP | helper de teste local; testes independentes entre si |
| DUPLICATE_BODY | `tests/test_job_parser_realistic.py:40 `test_empty_job_is_safe_and_reports_empty_description` | `tests/test_job_auto_parse.py::test_empty_job_text_does_not_break` | KEEP | helper de teste local; testes independentes entre si |
| DUPLICATE_TABLE | `tests/test_json_resume_interoperability.py:98` | `modules/ai/resume_extraction.py:15` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_local_ai_interoperability.py:61` | `modules/ai/task_registry.py:277` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_match_domain_weights.py:8` | `modules/domain_intelligence/domain_catalog.py:17` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_project_evidence_memory.py:21` | `modules/context/formatters.py:341` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_public_text_encoding.py:19` | `modules/github_analyzer/dependency_graph.py:99` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_public_text_encoding.py:20` | `modules/github_analyzer/file_filters.py:9` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_quick_mode_layout.py:7` | `modules/ui/advanced_mode.py:5` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_recommendation.py:16` | `apps/api/schemas/analysis.py:238` | CONSOLIDATED | `modules/schemas/job_analysis.Recommendation` (caf26ac) |
| DUPLICATE_TABLE | `tests/test_resume_parser.py:34` | `modules/parsers/job_description_parser.py:10` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_resume_skill_normalization.py:17` | `modules/parsers/job_description_parser.py:10` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
| DUPLICATE_TABLE | `tests/test_storage_migrations.py:28` | `modules/storage/health.py:283` | KEEP | oráculo de teste independente: não deve importar a tabela de produção |
