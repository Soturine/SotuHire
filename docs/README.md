# Documentação do SotuHire

Este é o índice documental do SotuHire. A home pública do site fica em [Início](index.md).

SotuHire é um copiloto de carreira local-first para análise de currículos, vagas, ATS,
Match Engine 2.0, oportunidades, histórico, portfolio, GitHub e evidências profissionais.

## Comece aqui

- [Home pública](index.md)
- [Visual preview v1.1](01-product/visual-preview.md)
- [Visão do produto](01-product/vision.md)
- [Roadmap atual](01-product/roadmap.md)
- [Setup local](07-development/setup.md)
- [Comandos de desenvolvimento](07-development/commands.md)
- [GitHub Pages vs app local](01-product/github-pages-site.md)
- [Frontend API Layer](02-architecture/frontend-api-layer.md)

## Produto

- [Demo v1.0](01-product/v1-demo.md)
- [Estratégia multiárea](01-product/multi-domain-product-strategy.md)
- [MVP](01-product/mvp-scope.md)
- [Histórias de usuário](01-product/user-stories.md)
- [Resume Tailor](01-product/resume-tailor.md)
- [Opportunity Fit Score](01-product/user-preferences-opportunity-fit.md)
- [Concurso Mode](01-product/concurso-mode.md)

## Frontend-ready

- [Overview frontend](08-frontend/README.md)
- [Arquitetura frontend-ready](08-frontend/frontend-architecture.md)
- [Lovable handoff](08-frontend/lovable-handoff.md)
- [Demo estática v1.1](08-frontend/static-demo.md)
- [Mapa de telas](08-frontend/screen-map.md)
- [API contract](08-frontend/api-contract.md)
- [Mock data contract](08-frontend/mock-data-contract.md)
- [Frontend rules](08-frontend/frontend-rules.md)
- [Application Intelligence](08-frontend/application-intelligence.md)

## Arquitetura e regras

- [Arquitetura](02-architecture/overview.md)
- [Data flow](02-architecture/data-flow.md)
- [Local Companion API](02-architecture/local-companion-api.md)
- [Frontend API Layer](02-architecture/frontend-api-layer.md)
- [Matching rules](03-business-rules/matching-rules.md)
- [ATS rules](03-business-rules/ats-rules.md)
- [Resume Tailor rules](03-business-rules/resume-tailor-rules.md)
- [Regras multiárea](03-business-rules/multi-domain-career-rules.md)
- [Privacidade da memória](03-business-rules/memory-privacy-rules.md)

## IA e prompts

- [Prompt Architecture](04-ai/prompt-architecture.md)
- [Prompt Registry](04-ai/prompt-registry.md)
- [Prompt Catalog](04-ai/prompt-catalog.md)
- [Structured Output](04-ai/structured-output-schema.md)
- [Prompts individuais](04-ai/prompts/README.md)
- [Gemini na análise real](04-ai/gemini-real-analysis-routing.md)

## Desenvolvimento

- [QA Testing](06-engineering/qa-testing.md)
- [Ruff](06-engineering/ruff.md)
- [CI/CD](06-engineering/ci-cd.md)
- [Security Privacy](06-engineering/security-privacy.md)
- [v0.10.0 AI Structured Extraction](07-development/v0.10.0-ai-structured-extraction.md)
- [v0.11.0 GitHub Analyzer 2.0](07-development/v0.11.0-github-analyzer-2.md)
- [v0.12.0 Match Engine 2.0](07-development/v0.12.0-match-engine-2.md)
- [v1.0.0 Stable Release](07-development/v1.0.0-stable-release.md)
- [v1.2.0 API Layer](07-development/v1.2.0-api-layer.md)

## Dados e fontes

- [Fontes públicas](05-data-sources/job-sources.md)
- [Brazilian job portals](05-data-sources/brazilian-job-portals.md)
- [Scraping strategy](05-data-sources/scraping-strategy.md)
- [Compliance and ethics](05-data-sources/compliance-and-ethics.md)
- [Hidden Jobs Radar](05-data-sources/hidden-jobs-radar.md)
- [Search Intelligence](05-data-sources/search-intelligence.md)
- [GitHub/Portfolio Analyzer](05-data-sources/github-portfolio-analyzer.md)

## Marcos

- v1.2.0 implementou FastAPI local, OpenAPI, endpoints `/api/v1` e Application Intelligence.
- v1.1.0 prepara handoff profissional para frontend moderno, contratos API, mocks e site público.
- v1.0.0 é a primeira versão estável e demonstrável, com Match Engine 2.0 exposto na UI,
  pesos por domínio, ATS/Tailor conectados ao match, demos fictícias multiárea e GitHub Pages.
- v0.12.0 implementou Match Engine 2.0.
- v0.11.0 implementou GitHub Analyzer 2.0.
- v0.10.0 implementou AI Structured Extraction e Domain Intelligence.

## Limites

SotuHire não promete contratação, não faz candidatura automática, não inventa experiências,
certificações ou registros profissionais, e mantém a pessoa usuária no controle da decisão.
