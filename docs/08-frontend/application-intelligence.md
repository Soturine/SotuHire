# Application Intelligence

Application Intelligence é a camada analítica futura do Kanban/tracker. Ela transforma
vagas salvas, candidaturas e resultados de matching em sinais úteis para decisão.

## Objetivo

Responder perguntas como:

- quais fontes trazem vagas com melhor match?
- quais requisitos aparecem mais nas vagas aplicadas?
- quais gaps críticos estão se repetindo?
- em quais etapas as candidaturas param?
- o perfil está evoluindo em direção às vagas desejadas?

## Métricas futuras

- total de vagas salvas;
- total de candidaturas aplicadas;
- vagas por status;
- vagas por fonte;
- match médio por status;
- ATS médio;
- taxa de resposta;
- taxa de entrevista;
- taxa de oferta;
- requisitos mais pedidos nas vagas aplicadas;
- requisitos mais pedidos nas vagas salvas;
- requisitos mais pedidos nas vagas com alto match;
- gaps críticos recorrentes;
- skills ausentes mais frequentes;
- requisitos por fonte;
- evolução semanal/mensal das candidaturas.

## Gráficos recomendados

- cards KPI;
- funil de candidatura;
- gráfico de barras para requisitos mais pedidos;
- gráfico de barras para gaps recorrentes;
- donut/pizza para status;
- linha temporal para candidaturas por semana;
- heatmap simples requisito x fonte;
- tabela ranqueada de skills.

## Base atual

O projeto já possui tracker, dashboard e `rank_applied_requirements`. A evolução deve
manter a agregação no backend/core e expor resultados prontos para o frontend.

## Evolução proposta

- `rank_requirements_by_status`
- `rank_requirements_by_source`
- `rank_missing_requirements`
- `rank_critical_gaps`
- `requirements_trend_over_time`

## Contratos relacionados

- `GET /api/v1/tracker/metrics`
- `GET /api/v1/tracker/requirements`
- `GET /api/v1/tracker/funnel`
- `GET /api/v1/tracker/sources`

## Regras

- Não calcular métricas oficiais no frontend.
- Não tratar ausência de evidência como competência confirmada.
- Mostrar quando há poucos dados para concluir tendência.
- Usar apenas dados locais autorizados.

