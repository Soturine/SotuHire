# Índice da documentação

Use este índice para localizar a documentação atual. Documentos de versões anteriores continuam disponíveis em **Histórico de desenvolvimento** e **Releases**, sem substituir as referências correntes.

## Comece aqui

- [Página inicial da documentação](index.md)
- [README do repositório no GitHub](https://github.com/Soturine/SotuHire#readme)
- [Visão do produto](01-product/vision.md)
- [Visão do produto v2](01-product/v2-product-vision.md)
- [Prévia visual v2](01-product/visual-preview.md)
- [Roadmap atual](01-product/roadmap.md)
- [Roteiro de demonstração](09-portfolio/demo-script.md)
- [Case study](09-portfolio/portfolio-case-study.md)

## Produto

- [Estratégia multiárea](01-product/multi-domain-product-strategy.md)
- [Histórias de usuário e casos de uso](01-product/user-stories.md)
- [Escopo atual](01-product/current-product-scope.md)
- [Fontes oficiais](02-architecture/official-opportunity-sources.md)
- [Taxonomias](02-architecture/taxonomy-layer.md)
- [Entrevistas e carreira](02-architecture/interview-and-career-workflows.md)
- [I18n e tema](02-architecture/i18n-and-theme.md)
- [Ajuda contextual](02-architecture/help-system.md)
- [Escopo do MVP histórico](history/mvp-scope.md)
- [GitHub Pages](01-product/github-pages-site.md)
- [Arquivo histórico do roadmap](01-product/roadmap-archive-through-v1.9.5.md)

## Arquitetura

- [Evidence Graph](02-architecture/evidence-graph.md)
- [Copilot sob aprovação humana](02-architecture/human-approved-copilot.md)
- [Fluxo de dados v2](02-architecture/data-flow.md)
- [Frontend v2 e design system](02-architecture/frontend-v2.md)
- [Portfólio e evidência acadêmica/profissional](02-architecture/portfolio-and-academic-evidence.md)
- [Jornada do usuário, Copilot e aprovações](05-user-guide/career-workflow.md)
- [Interoperabilidade com IA local](02-architecture/local-ai-interoperability.md)
- [Matching por domínio](02-architecture/domain-matching-policies.md)
- [Atualizações de taxonomia](02-architecture/taxonomy-updates.md)
- [Visão geral](02-architecture/overview.md)
- [Mapa de integração de módulos](02-architecture/module-integration-map.md)
- [Matriz verificável de capacidades](02-architecture/integration-capability-matrix.md)
- [Fluxo de dados](02-architecture/data-flow.md)
- [Career Context Engine](02-architecture/career-context-engine.md)
- [Linhagem e deduplicação](02-architecture/data-lineage-and-deduplication.md)
- [Frontend e API](02-architecture/frontend-api-layer.md)
- [Local Companion API](02-architecture/local-companion-api.md)
- [Extensão e Perfil Universal](02-architecture/extension-profile-bridge.md)
- [Fundação de editais](02-architecture/public-exams-foundation.md)
- [Application Lab](02-architecture/application-lab.md)
- [Resume Studio](02-architecture/resume-studio.md)
- [Application Readiness Report](02-architecture/application-readiness-report.md)

## Dados e persistência

- [Repository architecture](02-architecture/storage-repository-architecture.md)
- [Schema SQLite e migrações](02-architecture/sqlite-schema-and-migrations.md)
- [Snapshots de candidatura](02-architecture/application-snapshots.md)
- [Backup, restore e data health](02-architecture/backup-restore-and-data-health.md)
- [Storage e histórico](02-architecture/storage-and-history.md)
- [Auditoria de dados e integração](00-audit/v1.9.6-data-and-integration-audit.md)
- [Checklist de migração limpa](07-development/v1.9.6-clean-migration-checklist.md)

## IA

- [Orquestração, confiança e fallback](04-ai/ai-orchestration-and-confidence.md)
- [Catálogo de providers e modelos](02-architecture/ai-provider-model-catalog.md)
- [Prompt Registry](04-ai/prompt-registry.md)
- [Prompt Catalog](04-ai/prompt-catalog.md)
- [RAG e memória de carreira](04-ai/career-memory-rag.md)
- [Avaliação](04-ai/evaluation.md)
- [Plano de avaliação](04-ai/ai-evaluation-plan.md)
- [Golden datasets](09-testing/golden-datasets.md)
- [Arquitetura de avaliação](04-ai/ai-evaluation-architecture.md)
- [Governança de prompts](04-ai/prompt-governance.md)
- [Comparação de providers/modelos](04-ai/provider-model-comparison.md)
- [Feedback humano](04-ai/human-feedback.md)
- [Outcome Learning](02-architecture/outcome-learning.md)
- [Confiabilidade de providers](02-architecture/provider-reliability.md)
- [Taxonomia de erros](04-ai/provider-error-taxonomy.md)
- [Schema repair e fallback](04-ai/schema-repair-and-fallback.md)

## Fontes

- [Visão geral](05-data-sources/job-sources.md)
- [Conectores de fontes](05-data-sources/source-connectors.md)
- [Fontes públicas e importadores](05-data-sources/public-source-importers.md)
- [RSS e captura manual por URL](05-data-sources/rss-and-manual-url-connectors.md)
- [Estratégia de scraping público](05-data-sources/scraping-strategy.md)
- [GitHub e portfólio](05-data-sources/github-portfolio-analyzer.md)

## Extensão

- [Local Companion App](02-architecture/local-companion-app.md)
- [Regras de captura assistida](03-business-rules/browser-assisted-capture-rules.md)
- [Captura pela extensão](07-development/browser-extension-assisted-capture.md)
- [Publicação na Web Store](07-development/chrome-web-store-extension.md)
- [Análise GitHub/portfólio](07-development/extension-github-portfolio-analysis.md)
- [Testes da extensão](09-testing/browser-extension-testing.md)
- [README da extensão no GitHub](https://github.com/Soturine/SotuHire/tree/main/browser-extension)

## Testes e engenharia

- [Aceite de segurança v1.11.0](09-testing/v1.11.0-security-acceptance.md)
- [Benchmarks provider/domínio v1.11.0](09-testing/v1.11.0-provider-domain-benchmarks.md)
- [Segurança de dependências](06-engineering/dependency-security.md)
- [Licenciamento PDF](06-engineering/pdf-renderer-licensing.md)
- [QA e testes](06-engineering/qa-testing.md)
- [CI/CD](06-engineering/ci-cd.md)
- [Segurança e privacidade](06-engineering/security-privacy.md)
- [Ruff](06-engineering/ruff.md)
- [Testes de regressão](09-testing/regression-testing.md)
- [Testes de screenshot](09-testing/screenshot-testing.md)
- [Golden datasets](09-testing/golden-datasets.md)
- [Benchmarking de IA](09-testing/ai-benchmarking.md)
- [Testes do Application Lab](09-testing/application-lab-testing.md)
- [Testes do Resume Studio](09-testing/resume-studio-testing.md)

## Portfólio

- [Roteiro de demonstração](09-portfolio/demo-script.md)
- [Case study](09-portfolio/portfolio-case-study.md)
- [Galeria atual](01-product/visual-preview.md)

## Histórico de desenvolvimento

- [CHANGELOG no GitHub](https://github.com/Soturine/SotuHire/blob/main/CHANGELOG.md)
- [Histórico do roadmap](01-product/roadmap-history.md)
- [Arquivo do roadmap até a release anterior](01-product/roadmap-archive-through-v1.9.5.md)
- [Data reliability, migrações e backups](07-development/v1.9.6-data-reliability-migrations-backups.md)
- [Setup e desenvolvimento](07-development/setup.md)
- [Application Lab e Resume Studio v1.9.8](07-development/v1.9.8-guided-application-lab-resume-studio.md)
- [Validação externa v1.9.8](07-development/v1.9.8-external-provider-validation.md)

## Releases

- [Release atual — v2.0](releases/v2.0.md)
- [CHANGELOG](https://github.com/Soturine/SotuHire/blob/main/CHANGELOG.md)
- [Releases anteriores](https://github.com/Soturine/SotuHire/tree/main/docs/releases)
