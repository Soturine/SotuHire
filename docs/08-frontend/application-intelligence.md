# Application Intelligence

Application Intelligence e a camada analitica do Kanban/tracker. Ela transforma vagas salvas,
candidaturas e resultados de matching em sinais uteis para decisao.

## Objetivo

Responder perguntas como:

- quais fontes trazem vagas com melhor match?
- quais requisitos aparecem mais nas vagas aplicadas?
- quais gaps criticos estao se repetindo?
- em quais etapas as candidaturas param?
- o perfil esta evoluindo em direcao as vagas desejadas?

## Disponível na v1.3.0

- total de vagas salvas;
- total de candidaturas aplicadas;
- vagas por status;
- compatibilidade média por status;
- ATS medio;
- taxa de resposta;
- taxa de entrevista;
- taxa de oferta;
- requisitos mais pedidos;
- requisitos por fonte;
- skills/requisitos ausentes mais frequentes;
- gaps criticos recorrentes;
- funil salvo -> aplicado -> resposta -> entrevista -> oferta;
- fontes com volume, aplicacoes, entrevistas, compatibilidade média e top requirements.

## Funcoes de backend

As agregacoes ficam em `modules/tracker/dashboard.py`:

- `rank_requirements_by_status`
- `rank_requirements_by_source`
- `rank_missing_requirements`
- `rank_critical_gaps`
- `calculate_application_funnel`
- `calculate_source_metrics`

## Endpoints

- `GET /api/v1/tracker/metrics`
- `GET /api/v1/tracker/requirements`
- `GET /api/v1/tracker/funnel`
- `GET /api/v1/tracker/sources`

## Graficos recomendados

- cards KPI;
- funil de candidatura;
- barras para requisitos mais pedidos;
- barras para gaps recorrentes;
- donut/pizza para status;
- tabela ranqueada de sources;
- tabela ranqueada de skills.

## Evolucao futura

- trend semanal/mensal de candidaturas;
- trend de requisitos ao longo do tempo;
- heatmap requisito x fonte;
- comparacao por dominio profissional;
- metricas de tempo entre etapas.

## Mocks relacionados

- `docs/assets/mock-api/tracker-metrics.json`
- `docs/assets/mock-api/tracker-requirements.json`
- `docs/assets/mock-api/tracker-funnel.json`
- `docs/assets/mock-api/tracker-sources.json`

## Demo estatica

A pagina [Static demo](static-demo.md) mostra uma representacao visual desses contratos usando
apenas dados ficticios.

## Regras

- Nao calcular metricas oficiais no frontend.
- Nao tratar ausencia de evidencia como competencia confirmada.
- Mostrar quando ha poucos dados para concluir tendencia.
- Usar apenas dados locais autorizados.
