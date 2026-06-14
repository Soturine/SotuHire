# Local build report

## Atualização

Esta versão atualiza a documentação do SotuHire para incluir:

- estratégia de scraping responsável;
- conectores de fontes;
- benchmark de players e projetos similares;
- Ruff como linter/formatter oficial do projeto;
- `pyproject.toml`;
- GitHub Actions;
- `.pre-commit-config.yaml`;
- comandos de qualidade;
- variáveis de ambiente para scraping controlado.

## Arquivos adicionados

```text
docs/05-data-sources/scraping-strategy.md
docs/05-data-sources/source-connectors.md
docs/06-engineering/ruff.md
docs/06-engineering/ci-cd.md
docs/08-benchmark/players-and-inspirations.md
pyproject.toml
.github/workflows/ci.yml
.pre-commit-config.yaml
```

## Data

Gerado em: 2026-06-12T06:29:01


## Atualização: Lattes, ATS e portais brasileiros

Foi adicionada uma nova camada de documentação para:

- separar currículo ATS de Currículo Lattes;
- tratar GitHub, LinkedIn e portfólio como fontes complementares;
- mapear portais brasileiros de vagas e estágio;
- planejar conectores por prioridade;
- registrar riscos e abordagens por fonte.

Novos arquivos:

- `docs/03-business-rules/resume-types.md`;
- `docs/05-data-sources/brazilian-job-portals.md`;
- `docs/05-data-sources/portal-connector-roadmap.md`.

---

# Atualização expandida

Esta revisão adicionou documentação e módulos para:

- Search Intelligence;
- fontes alternativas;
- Social Post Discovery;
- RAG Memory;
- AI Provider Strategy;
- Profile Score;
- GitHub/Portfolio Analyzer;
- Job Tracker Kanban;
- Follow-up Assistant;
- Alerts Roadmap;
- Browser Extension Roadmap;
- projetos de referência.

Garantia aplicada nesta geração:

- nenhum arquivo existente foi removido;
- nenhum documento Markdown existente teve número de linhas reduzido;
- novos docs foram adicionados em subdiretórios existentes;
- módulos Python foram adicionados como base inicial testável;
- novos links e diagramas Mermaid foram incluídos.

---

# Validação local da v0.8.0

Executado em 2026-06-14 após a implementação de Career Memory e RAG local:

| Verificação | Resultado |
| --- | --- |
| Pyright | 0 erros, 0 warnings |
| Ruff check | aprovado |
| Ruff format check | 196 arquivos formatados |
| Pytest | 157 testes aprovados |
| MkDocs strict | build aprovado |
| Streamlit health | HTTP 200, resposta `ok` |
| Capturas v0.8.0 | quatro PNGs fictícios inspecionados |

A validação cobre análise com e sem memória, opt-in do Gemini, feedback, export/import, perfil,
Search Intelligence, Hidden Jobs Radar, tracker, dashboard, documentação e navegação Streamlit.
