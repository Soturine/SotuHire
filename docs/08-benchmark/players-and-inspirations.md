# Players, programas e projetos de referência

## Objetivo

Este documento junta referências de mercado e projetos open-source que ajudam a posicionar o SotuHire.

A ideia não é copiar um produto. A ideia é entender:

- quais features já são comuns;
- onde existe oportunidade de diferenciação;
- quais riscos evitar;
- quais decisões de UX e arquitetura fazem sentido.

## Players comerciais

### Teal

Foco provável:

- resume builder;
- job tracker;
- keyword matching;
- resume/job description match;
- Chrome extension;
- cover letter;
- organização da busca.

O que inspira no SotuHire:

- tracker de vagas;
- scanner de palavras-chave;
- extensão assistiva;
- histórico de candidatura;
- score por vaga.

### Jobscan

Foco provável:

- ATS checker;
- resume score;
- keyword matching;
- LinkedIn profile optimization;
- cover letter;
- job tracker.

O que inspira:

- separar ATS Score de Match Score;
- mostrar palavras-chave ausentes;
- indicar onde inserir palavras-chave;
- relatório visual.

### Simplify

Foco provável:

- job search;
- autofill;
- extension;
- resume builder;
- job tracker;
- job matches.

O que inspira:

- extensão de navegador;
- salvar vaga rapidamente;
- reduzir trabalho repetitivo;
- UX simples.

Cuidado:

- SotuHire deve evitar auto-apply em massa.

### Huntr

Foco provável:

- job tracker;
- contact tracker;
- interview tracker;
- resume tailoring;
- keyword scanner;
- metrics.

O que inspira:

- status de candidatura;
- contatos por vaga;
- métricas de funil;
- organização tipo CRM de carreira.

### Jobright

Foco provável:

- AI job copilot;
- job matching;
- tailored resume;
- networking/referrals.

O que inspira:

- abordagem para recrutador;
- mensagens para pessoas da empresa;
- recomendação de estratégia:
  - aplicar direto;
  - pedir indicação;
  - melhorar currículo antes.

### LoopCV / LazyApply / Sonara

Foco provável:

- auto-apply;
- automação agressiva;
- envio em volume;
- candidaturas em lote.

O que inspira apenas como anti-exemplo:

- existe demanda por automação;
- mas auto-apply pode virar spam;
- o SotuHire deve ser mais explicável, cuidadoso e revisável.

## Projetos open-source

### Resume Matcher

Referência importante para:

- upload de currículo;
- job description matching;
- IA para melhorias;
- score;
- possível backend/frontend mais robusto.

O que estudar:

- estrutura do README;
- arquitetura;
- screenshots;
- forma de mostrar match;
- suporte a LLM local.

### OpenResume

Referência para:

- privacidade;
- resume parser;
- currículo ATS-friendly;
- uso local;
- feedback visual.

O que estudar:

- UX de importação;
- parse de currículo;
- visão local-first.

### Reactive Resume

Referência para:

- builder de currículo;
- templates;
- self-hosting;
- exportação;
- privacidade;
- multi-idioma.

O que estudar:

- organização de dados do currículo;
- exportação;
- controle do usuário sobre os dados.

### AIHawk

Referência técnica, mas não referência de produto.

O que estudar:

- automação;
- estrutura de agente;
- limites de abordagem.

O que evitar:

- auto-apply em massa;
- dependência de plataforma fechada;
- risco de bloqueio;
- candidatura sem revisão humana.

## Diferenciação do SotuHire

O SotuHire não deve competir apenas como “mais um ATS checker”.

Diferenciais sugeridos:

1. foco em estágio/júnior/trainee;
2. foco em tecnologia, IA, dados, automação, QA e suporte;
3. regras explícitas de senioridade;
4. radar de vagas escondidas em posts;
5. scraping responsável;
6. explicação do match;
7. privacidade/local-first;
8. revisão humana;
9. testes e Clean Code como parte do portfólio;
10. documentação técnica forte.

## Feature matrix

| Feature | SotuHire | Teal/Jobscan/Huntr/Simplify | Auto-apply tools |
|---|---:|---:|---:|
| ATS checker | Sim | Sim | Às vezes |
| Match CV x vaga | Sim | Sim | Sim |
| Job tracker | Planejado | Sim | Às vezes |
| Hidden Jobs Radar | Diferencial | Pouco comum | Não é foco |
| Scraping responsável | Sim | Interno/fechado | Variável |
| Auto-apply em massa | Não | Às vezes | Sim |
| Revisão humana | Sim | Sim | Nem sempre |
| Foco estágio/júnior tech | Sim | Genérico | Genérico |
| Regras testáveis | Sim | Não visível | Não visível |
| Open-source/portfólio | Sim | Não | Alguns |

## O que incluir no roadmap por inspiração

### Inspirado em Teal/Huntr

- tracker de vagas;
- status;
- contatos;
- entrevistas;
- métricas.

### Inspirado em Jobscan

- ATS Score;
- keyword gaps;
- relatório de otimização;
- comparação por requisito.

### Inspirado em Simplify

- extensão assistiva;
- salvar vaga;
- leitura rápida da página aberta.

### Inspirado em OpenResume/Reactive Resume

- privacidade;
- exportação;
- modelo estruturado do currículo;
- templates no futuro.

### Inspirado em Resume Matcher

- matching robusto;
- screenshots;
- suporte a LLM local;
- demo clara.

## Próximas features recomendadas

1. MVP manual com Streamlit.
2. JSON estruturado.
3. regras determinísticas.
4. testes e Ruff.
5. fixtures de vagas.
6. job tracker.
7. scraping de páginas públicas simples.
8. hidden jobs radar.
9. extensão assistiva.
10. documentação com screenshots.
