# Documentação do SotuHire

Bem-vindo à documentação do SotuHire, um copiloto de carreira local-first para análise de
currículos, vagas, ATS, oportunidades, histórico, portfólio, GitHub e evidências profissionais.
A visão atual é multiárea: tecnologia é uma das frentes, mas o produto também cobre saúde,
engenharias, educação, administração, finanças, marketing, logística, indústria, design,
estágios, jovem aprendiz, transição de carreira e outros perfis.

## Comece aqui

- [Visão do produto](01-product/vision.md)
- [Roadmap atual](01-product/roadmap.md)
- [Estratégia multiárea](01-product/multi-domain-product-strategy.md)
- [Arquitetura](02-architecture/overview.md)
- [Setup local](07-development/setup.md)
- [Comandos de desenvolvimento](07-development/commands.md)

## Produto

- [Visão](01-product/vision.md)
- [Roadmap](01-product/roadmap.md)
- [Histórico do roadmap](01-product/roadmap-history.md)
- [Estratégia multiárea](01-product/multi-domain-product-strategy.md)
- [MVP](01-product/mvp-scope.md)
- [Histórias de usuário](01-product/user-stories.md)
- [Rotina inteligente de busca](01-product/job-search-routine.md)
- [Resume Tailor](01-product/resume-tailor.md)
- [Opportunity Fit Score](01-product/user-preferences-opportunity-fit.md)
- [Concurso Mode](01-product/concurso-mode.md)

## IA e prompts

- [Prompt Architecture](04-ai/prompt-architecture.md)
- [Prompt Registry](04-ai/prompt-registry.md)
- [Prompt Catalog](04-ai/prompt-catalog.md)
- [AI Orchestration and Confidence](04-ai/ai-orchestration-and-confidence.md)
- [Structured Output](04-ai/structured-output-schema.md)
- [Prompting](04-ai/prompting.md)
- [Evaluation](04-ai/evaluation.md)
- [RAG Memory Architecture](04-ai/rag-memory-architecture.md)
- [Career Memory e RAG local](04-ai/career-memory-rag.md)
- [Calibração de evidências](04-ai/evidence-calibration.md)
- [Provider Strategy](04-ai/provider-strategy.md)
- [Gemini Structured Output](04-ai/gemini-structured-output.md)
- [Setup local do Gemini](04-ai/gemini-local-setup.md)
- [Gemini na análise real](04-ai/gemini-real-analysis-routing.md)
- [JSON Resume e Pydantic](04-ai/json-resume-and-pydantic.md)
- [ML avançado futuro](04-ai/advanced-ml-future.md)

## Prompts individuais

- [Índice de prompts](04-ai/prompts/README.md)
- [Resume Extraction v1](04-ai/prompts/resume-extraction-v1.md)
- [Job Extraction Multi-Domain v1](04-ai/prompts/job-extraction-multi-domain-v1.md)
- [Domain Classification v1](04-ai/prompts/domain-classification-v1.md)
- [Match Analysis Evidence-Based v1](04-ai/prompts/match-analysis-evidence-based-v1.md)
- [ATS Analysis v1](04-ai/prompts/ats-analysis-v1.md)
- [Resume Tailor v1](04-ai/prompts/resume-tailor-v1.md)
- [GitHub Repo Analysis v2](04-ai/prompts/github-repo-analysis-v2.md)
- [GitHub Profile Analysis v1](04-ai/prompts/github-profile-analysis-v1.md)
- [Portfolio Gap Analysis v1](04-ai/prompts/portfolio-gap-analysis-v1.md)
- [Hidden Job Detection v1](04-ai/prompts/hidden-job-detection-v1.md)
- [Career Advice v1](04-ai/prompts/career-advice-v1.md)

## Arquitetura

- [Overview](02-architecture/overview.md)
- [Data flow](02-architecture/data-flow.md)
- [Folder structure](02-architecture/folder-structure.md)
- [Architecture decisions](02-architecture/architecture-decisions.md)
- [MVP core schemas](02-architecture/mvp-core-schemas.md)
- [Local companion app](02-architecture/local-companion-app.md)
- [Local Companion API](02-architecture/local-companion-api.md)
- [Background jobs](02-architecture/background-jobs.md)
- [Parsers](02-architecture/parsers.md)
- [Semântica do parser](02-architecture/parser-semantics.md)
- [Fluxo automático](02-architecture/auto-flow.md)
- [Storage e histórico](02-architecture/storage-and-history.md)
- [Pipeline de coleta de oportunidades](02-architecture/opportunity-collection-pipeline.md)
- [Modo rápido vs. avançado](02-architecture/quick-vs-advanced-mode.md)
- [Career Memory Store](02-architecture/career-memory-store.md)

## Regras de negócio

- [Matching](03-business-rules/matching-rules.md)
- [ATS](03-business-rules/ats-rules.md)
- [Multi-domain career rules](03-business-rules/multi-domain-career-rules.md)
- [Tracker e Kanban](07-development/job-tracker-kanban.md)
- [Search Intelligence](05-data-sources/search-intelligence.md)
- [Job filtering](03-business-rules/job-filtering.md)
- [Resume types](03-business-rules/resume-types.md)
- [Profile score](03-business-rules/profile-score.md)
- [Resume Tailor rules](03-business-rules/resume-tailor-rules.md)
- [Opportunity Fit Score](03-business-rules/opportunity-fit-score.md)
- [Public exam rules](03-business-rules/public-exam-rules.md)
- [Privacidade da memória](03-business-rules/memory-privacy-rules.md)
- [Regras de captura assistida](03-business-rules/browser-assisted-capture-rules.md)

## Dados e fontes

- [Fontes públicas](05-data-sources/job-sources.md)
- [Brazilian job portals](05-data-sources/brazilian-job-portals.md)
- [Portal connector roadmap](05-data-sources/portal-connector-roadmap.md)
- [Source connectors](05-data-sources/source-connectors.md)
- [Scraping strategy](05-data-sources/scraping-strategy.md)
- [Authenticated browser crawling](05-data-sources/authenticated-browser-crawling.md)
- [Compliance and ethics](05-data-sources/compliance-and-ethics.md)
- [Hidden Jobs Radar](05-data-sources/hidden-jobs-radar.md)
- [Search Intelligence foundation](05-data-sources/search-intelligence-foundation.md)
- [Hidden Jobs Radar safe mode](05-data-sources/hidden-jobs-radar-safe-mode.md)
- [RSS e URL manual](05-data-sources/rss-and-manual-url-connectors.md)
- [Alternative job boards](05-data-sources/alternative-job-boards.md)
- [Social post discovery](05-data-sources/social-post-discovery.md)
- [GitHub/Portfolio Analyzer](05-data-sources/github-portfolio-analyzer.md)
- [JobSpy experimental reference](05-data-sources/jobspy-experimental-reference.md)

## Desenvolvimento

- [Setup](07-development/setup.md)
- [Testes e QA](06-engineering/qa-testing.md)
- [Commands](07-development/commands.md)
- [Contributing](07-development/contributing.md)
- [Clean Code e SOLID](06-engineering/clean-code-solid.md)
- [Ruff](06-engineering/ruff.md)
- [CI/CD](06-engineering/ci-cd.md)
- [Security Privacy](06-engineering/security-privacy.md)
- [Avoid overengineering](06-engineering/avoid-overengineering.md)
- [Repository metadata](07-development/repository-metadata.md)
- [v0.10.0 AI Structured Extraction](07-development/v0.10.0-ai-structured-extraction.md)
- [v0.11.0 GitHub Analyzer 2.0](07-development/v0.11.0-github-analyzer-2.md)
- [v0.12.0 Match Engine 2.0](07-development/v0.12.0-match-engine-2.md)

## Marcos documentados

- v0.9.0 já é um produto local-first funcional, com análise local, ATS, matching, tracker,
  dashboard, memória, RAG, extensão, Local Companion API, Hidden Jobs Radar e análise de
  GitHub/portfólio.
- v0.9.1 é uma versão documental: navegação, README, CHANGELOG e prompt playbooks.
- v0.10.0 está planejada para AI Structured Extraction e Domain Intelligence, com Prompt Registry,
  JSON Guard, schemas Pydantic, extração estruturada de currículo/vaga e confiança por campo.
- v0.11.0 está planejada como GitHub Analyzer 2.0, com API, árvore completa, sampler, contexto de
  arquivos, prompt estruturado, evidence index e score de portfólio.
- v0.12.0 está planejada como Match Engine 2.0, saindo de keyword matching simples para matching por
  requisitos, evidências, domínio, senioridade, gaps críticos e competências transferíveis.
- v1.0 é a meta de versão generalista estável de inteligência de carreira.

## Auditoria e histórico

- [Auditoria de documentação](00-audit/documentation-audit.md)
- [Relatório local](00-audit/local-build-report.md)
- [Atualização pós-v0.9.0](00-audit/v0.9-roadmap-docs-update-summary.md)
- O changelog do repositório fica na raiz do projeto.

## Observação sobre escopo

SotuHire mantém a pessoa usuária no controle, não inventa experiências, não faz candidatura
automática e não deve ser tratado como ferramenta exclusiva de TI. Recursos futuros documentados no
roadmap são planejamento técnico; quando algo ainda não está implementado, a documentação deve
tratar como planejado ou futuro.
