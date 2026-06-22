# Mock data contract

Os mocks oficiais ficam em `docs/assets/mock-api/` e usam apenas dados fictícios.

Eles existem para Lovable e outros frontends prototiparem telas reais, estados vazios e estados de
erro sem depender da API local estar rodando. Desde a v1.3.0, o frontend moderno existe em
`apps/web`; os mocks devem continuar alinhados ao contrato de `docs/08-frontend/api-contract.md`.

## Regras dos mocks

- não usar nomes reais de candidatos;
- não usar currículos reais;
- não usar empresas reais como se fossem empregadoras do exemplo;
- não incluir API keys, tokens, paths locais ou dados sensíveis;
- manter campos próximos dos contratos de API;
- preservar linguagem anti-invenção em ATS e Tailor;
- incluir estados suficientes para cards, listas, gráficos e tabelas.

## Arquivos

- `health.json`: status da API local.
- `resume-extraction.json`: perfil profissional fictício extraído.
- `job-extraction.json`: vaga fictícia estruturada.
- `match-result.json`: resultado de Análise de Compatibilidade.
- `ats-review.json`: revisão ATS com keywords por evidência.
- `resume-tailor.json`: sugestões seguras de currículo.
- `github-repo-analysis.json`: evidências de repositório público fictício.
- `tracker-jobs.json`: vagas fictícias para Kanban.
- `tracker-metrics.json`: KPIs do tracker.
- `tracker-requirements.json`: requisitos, gaps e dados para gráficos.
- `tracker-funnel.json`: funil de candidatura.
- `tracker-sources.json`: fontes de vagas.

## Uso recomendado no frontend

1. Carregar mocks em desenvolvimento.
2. Renderizar estados de sucesso.
3. Criar também estados vazios e de erro no frontend.
4. Trocar a fonte de dados por HTTP client apontando para `http://127.0.0.1:8787/api/v1`.
5. Validar divergencias usando o OpenAPI em `/openapi.json`.
