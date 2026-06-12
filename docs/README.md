# SotuHire Documentation

Esta pasta contém a documentação técnica e de produto do SotuHire.

## Mapa

- `00-audit`: auditoria da documentação;
- `01-product`: visão, escopo, histórias e roadmap;
- `02-architecture`: arquitetura, pastas, fluxo de dados e decisões;
- `03-business-rules`: regras de match, ATS e filtragem;
- `04-ai`: prompts, schemas e avaliação;
- `05-data-sources`: fontes, scraping, conectores, Hidden Jobs Radar e compliance;
- `06-engineering`: Clean Code, SOLID, QA, Ruff, CI/CD, privacidade e anti-overengineering;
- `07-development`: setup, contribuição e comandos;
- `08-benchmark`: players, programas e projetos de referência.

## Rodar documentação

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Depois abra o endereço mostrado no terminal.


## Novos documentos importantes

- [`03-business-rules/resume-types.md`](03-business-rules/resume-types.md): currículo ATS, Currículo Lattes, LinkedIn, GitHub e portfólio.
- [`05-data-sources/brazilian-job-portals.md`](05-data-sources/brazilian-job-portals.md): matriz de portais brasileiros como Gupy, InfoJobs, Indeed, CIEE, Companhia de Estágios, InHire, Vagas.com, Catho e outros.
- [`05-data-sources/portal-connector-roadmap.md`](05-data-sources/portal-connector-roadmap.md): plano de implementação dos conectores.

---

## Novos grupos de documentação

### Produto

- [Rotina Inteligente de Busca](01-product/job-search-routine.md)

### IA

- [RAG e Memória de Carreira](04-ai/rag-memory-architecture.md)
- [Provider Strategy](04-ai/provider-strategy.md)

### Regras de negócio

- [Profile Score](03-business-rules/profile-score.md)

### Fontes de dados

- [Search Intelligence](05-data-sources/search-intelligence.md)
- [Fontes Alternativas](05-data-sources/alternative-job-boards.md)
- [Social Post Discovery](05-data-sources/social-post-discovery.md)
- [GitHub/Portfolio Analyzer](05-data-sources/github-portfolio-analyzer.md)

### Desenvolvimento

- [Job Tracker Kanban](07-development/job-tracker-kanban.md)
- [Follow-up Assistant](07-development/follow-up-assistant.md)
- [Alerts Roadmap](07-development/alerts-roadmap.md)
- [Browser Extension Roadmap](07-development/browser-extension-roadmap.md)
- [Profile Analyzer Roadmap](07-development/profile-analyzer-roadmap.md)

### Benchmark

- [Projetos de Referência](08-benchmark/reference-projects.md)
