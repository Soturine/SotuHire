# Projetos de Referência e Inspirações Técnicas

Este documento registra projetos que inspiram partes específicas do SotuHire.

O objetivo não é copiar. O objetivo é entender padrões bons e adaptar para uma arquitetura própria.

## RepoLogs GitHub Extension

Link: <https://github.com/VictoriaSCorreia/RepoLogs_GithubExtension>

Inspira:

- extensão Chrome contextual;
- botão injetado em página aberta;
- análise de repositório público;
- seleção inteligente de arquivos;
- score estruturado;
- análise de arquitetura, segurança e qualidade;
- cache por repositório/commit.

Aplicação no SotuHire:

- GitHub Portfolio Analyzer;
- Portfolio Score;
- extensão assistiva;
- análise de README, testes, CI e stack.

## Automated Job Search Scraper

Link: <https://github.com/VictoriaSCorreia/AUTOMATED_JOBSEACRH_SCRAPER>

Inspira:

- coleta automática de vagas;
- Selenium para páginas dinâmicas;
- suporte a múltiplas fontes por seletores;
- CSV;
- alertas via Telegram;
- filtro por data.

Aplicação no SotuHire:

- Opportunity Collector;
- alertas;
- scraping responsável;
- conectores isolados;
- deduplicação e normalização.

## LinkedIn Profile Score

Link: <https://github.com/henriquesantanati/linkedin-profile-score>

Inspira:

- análise por exportação oficial do LinkedIn;
- score 0-100;
- recomendações acionáveis;
- privacidade/local-first;
- checklist manual.

Aplicação no SotuHire:

- LinkedIn Score;
- Profile Score Engine;
- leitura de CSV exportado;
- alinhamento LinkedIn x currículo x vaga.

## Resume Matcher

Link: <https://github.com/srbhr/Resume-Matcher>

Inspira:

- match currículo-vaga;
- resume tailoring;
- IA aplicada a currículo;
- arquitetura backend/frontend;
- uso de modelos locais e provedores.

## OpenResume

Link: <https://github.com/xitanggg/open-resume>

Inspira:

- privacidade;
- parser de currículo;
- visualização de currículo;
- foco em ATS.

## Reactive Resume

Link: <https://github.com/AmruthPillai/Reactive-Resume>

Inspira:

- builder de currículo;
- templates;
- self-host;
- exportação;
- controle de dados.

## AIHawk

Link: <https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk>

Inspira tecnicamente a discussão sobre agentes de candidatura, mas o SotuHire não deve seguir o caminho de auto-apply agressivo.

Aplicação no SotuHire:

- documentar limites;
- reforçar revisão humana;
- evitar automação de candidatura em massa.

## Teal, Huntr, Simplify e Jobscan

Links:

- <https://www.tealhq.com/>
- <https://huntr.co/>
- <https://simplify.jobs/>
- <https://www.jobscan.co/>

Inspiram:

- job tracker;
- score ATS;
- keywords;
- extensão;
- organização de candidaturas;
- dashboard.

## Diferencial do SotuHire

O SotuHire junta:

```text
ATS + Match + RAG + Search Intelligence + Hidden Jobs Radar + Job Tracker + LinkedIn Score + Portfolio Score + Scraping responsável + Extensão assistiva
```

Mas mantém limites:

```text
sem auto-apply em massa
sem scraping logado agressivo
sem mensagens automáticas
sem prometer contratação
sem inventar experiência
```
