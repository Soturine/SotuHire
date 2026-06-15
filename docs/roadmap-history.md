# Histórico do Roadmap

Este documento preserva a evolução histórica do SotuHire.

O roadmap atual fica em:

```txt
docs/01-product/roadmap.md
```

## Origem

O projeto começou com a ideia de ajudar candidatos a encontrar vagas, comparar currículos e melhorar aderência a oportunidades.

A visão inicial era naturalmente mais próxima de tecnologia, desenvolvimento, dados, automação e estágio, por ser o contexto inicial do projeto e dos exemplos usados.

Com a evolução do produto, o escopo mudou para um copiloto de carreira multiárea, local-first e explicável.

## MVP inicial

O MVP inicial focava em:

- entrada manual de currículo;
- entrada manual de vaga;
- análise local;
- score simples;
- sugestões iniciais;
- interface Streamlit;
- persistência local básica.

## Evolução até v0.4

As primeiras versões consolidaram:

- parser local;
- análise de vaga;
- Match Score inicial;
- ATS Score inicial;
- Opportunity Fit Score;
- Risk Score;
- Resume Tailor;
- documentação inicial;
- testes básicos.

## Evolução v0.5 a v0.8

As versões intermediárias adicionaram:

- Career Memory;
- perfil profissional persistente;
- RAG lexical local;
- tracker de candidaturas;
- dashboard;
- Search Intelligence;
- Hidden Jobs Radar;
- melhorias em deduplicação;
- melhorias em importação manual e assistida;
- documentação expandida;
- mais testes.

## v0.9.0

A v0.9.0 consolidou a base mais ampla do produto:

- extensão assistiva;
- Local Companion API;
- integração com navegador;
- análise inicial de GitHub e portfólio;
- importação assistida;
- integração com tracker;
- Gemini opcional;
- documentação extensa;
- foco em privacidade e local-first.

## Aprendizados históricos

### 1. Evitar automação agressiva

O produto fica mais forte quando é um copiloto com humano no controle, não um bot de candidatura automática.

### 2. Heurísticas são úteis, mas insuficientes

Heurísticas locais são boas para fallback, velocidade e testes, mas não devem ser o limite da inteligência do produto.

### 3. IA precisa de contrato

Prompts soltos geram respostas difíceis de validar. O caminho correto é usar prompts versionados, JSON estruturado, schemas e validação.

### 4. Multiárea precisa ser intencional

Para o SotuHire funcionar além de TI, o sistema precisa entender domínio, tipo de requisito, credenciais, ferramentas, equipamentos, normas e competências transferíveis.

### 5. GitHub e portfólio são evidências

Projetos não devem ser apenas anexos. Eles devem virar evidências profissionais conectadas ao currículo e às vagas.
