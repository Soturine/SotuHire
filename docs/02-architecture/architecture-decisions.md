# Decisões arquiteturais

Este documento registra decisões importantes para evitar que o projeto cresça sem direção.

## ADR 001 - Começar com Streamlit

### Decisão

Usar Streamlit no MVP inicial.

### Motivo

Streamlit permite criar interface rapidamente em Python, sem backend separado e sem frontend complexo. Para validar upload de currículo, campo de texto e relatório, é suficiente.

### Consequências

Positivas:

- desenvolvimento rápido;
- menos boilerplate;
- fácil para demo;
- bom para portfólio inicial.

Negativas:

- menos flexível que React;
- pode ficar limitado para produto maior;
- não é ideal para arquitetura multiusuário complexa.

## ADR 002 - Não iniciar com React + FastAPI

### Decisão

Não usar React + FastAPI no primeiro MVP.

### Motivo

O núcleo do produto é análise de currículo e vaga, não frontend complexo. Adicionar duas stacks cedo aumenta custo e atrasa validação.

## ADR 003 - Resposta de IA em JSON

### Decisão

Usar saída estruturada em JSON/schema.

### Motivo

Texto livre é ruim para UI, testes e validação. JSON permite mostrar score, listas e campos com mais controle.

## ADR 004 - Regras de negócio fora da IA

### Decisão

Senioridade, termos de corte e recomendações determinísticas devem ficar em código.

### Motivo

A IA pode variar. Regras centrais precisam ser testáveis e previsíveis.

## ADR 005 - Não fazer candidatura automática em massa

### Decisão

O sistema não deve aplicar automaticamente para vagas em massa.

### Motivo

Isso reduz risco de spam, erro de candidatura, violação de termos de plataformas e perda de controle pelo usuário.

## ADR 006 - Scraping com limites

### Decisão

Scraping só deve ser considerado para páginas públicas e permitido pelo contexto técnico/legal. Não deve haver bypass de autenticação, captcha, rate limit ou coleta agressiva.

### Motivo

O objetivo é portfólio profissional, não ferramenta de evasão.

## ADR 007 - Testar primeiro regras determinísticas

### Decisão

O primeiro foco de QA é testar funções que não dependem de LLM.

### Motivo

Testes de IA são mais difíceis e instáveis. Regras determinísticas dão retorno rápido e aumentam confiança.
