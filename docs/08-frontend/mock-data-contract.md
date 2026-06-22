# Mock data contract

Os mocks oficiais ficam em `docs/assets/mock-api/` e usam apenas dados fictícios.

Eles existem para Lovable e outros frontends prototiparem telas reais antes da API v1
estar implementada.

## Regras dos mocks

- não usar nomes reais de candidatos;
- não usar currículos reais;
- não usar empresas reais como se fossem empregadoras do exemplo;
- não incluir API keys, tokens, paths locais ou dados sensíveis;
- manter campos próximos dos contratos de API;
- preservar linguagem anti-invenção em ATS e Tailor;
- incluir estados suficientes para cards, listas, gráficos e tabelas.

## Arquivos

- `health.json`: status da API local futura.
- `resume-extraction.json`: perfil profissional fictício extraído.
- `job-extraction.json`: vaga fictícia estruturada.
- `match-result.json`: resultado Match Engine 2.0.
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
4. Trocar a fonte de dados por HTTP client quando a API real existir.

