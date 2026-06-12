# Escopo dos MVPs

## Estratégia geral

O SotuHire deve evoluir em etapas pequenas. O erro mais perigoso seria tentar começar com dashboard, banco, scrapers, login, extensão Chrome, alertas e IA avançada ao mesmo tempo. Isso viraria overengineering antes mesmo do produto validar o núcleo.

A ordem correta é:

1. validar análise de currículo + vaga;
2. estruturar resposta da IA;
3. aplicar regras de negócio;
4. testar lógica determinística;
5. salvar histórico;
6. buscar vagas;
7. analisar posts;
8. criar extensão ou automações.

## MVP 1 - Análise manual de currículo e vaga

### Objetivo

Validar se o sistema consegue analisar uma vaga colada manualmente e produzir um relatório útil.

### Entrada

- currículo PDF;
- descrição da vaga colada pelo usuário;
- área alvo opcional;
- preferências opcionais, como remoto, híbrido ou presencial.

### Saída

- score de match;
- recomendação;
- pontos fortes;
- pontos fracos;
- gaps técnicos;
- gaps de senioridade;
- palavras-chave sugeridas;
- análise ATS básica;
- mensagem curta para recrutador.

### Fora do escopo

- buscador automático;
- login em plataforma;
- candidatura automática;
- histórico em banco;
- extensão de navegador;
- alertas.

## MVP 2 - Resposta estruturada e UI melhor

### Objetivo

Trocar texto solto da IA por JSON/schema validado, permitindo uma UI mais clara.

### Funcionalidades

- schema Pydantic para resposta;
- validação de campos;
- `st.metric` para score;
- barra de progresso;
- tabelas para pontos fortes e gaps;
- tratamento de erro quando a IA retorna JSON inválido.

## MVP 3 - Regras de negócio determinísticas

### Objetivo

Separar o que é decisão de negócio do que é interpretação da IA.

### Funcionalidades

- arquivo `business_rules.py`;
- termos que reduzem match;
- termos que aumentam prioridade;
- corte por senioridade;
- classificação por score;
- testes com `pytest`.

## MVP 4 - Histórico local

### Objetivo

Salvar análises para o usuário comparar vagas.

### Funcionalidades

- SQLite;
- tabela de currículos analisados;
- tabela de vagas;
- tabela de análises;
- filtros por score, data e recomendação.

## MVP 5 - Buscador de vagas públicas

### Objetivo

Encontrar oportunidades em fontes permitidas ou públicas sem depender de automação logada.

### Funcionalidades

- coleta de páginas públicas;
- normalização de título, empresa, local e link;
- deduplicação;
- análise por match;
- dashboard.

## MVP 6 - Radar de Vagas Escondidas

### Objetivo

Identificar oportunidades em posts informais, textos de recrutadores e indicações.

### Funcionalidades

- entrada manual de post;
- classificação `is_job_post`;
- extração de cargo, empresa, contato e modalidade;
- match com currículo;
- geração de mensagem de abordagem.

## MVP 7 - Extensão de navegador

### Objetivo

Permitir que o usuário analise a página que ele mesmo abriu.

### Funcionalidades

- botão “Analisar com SotuHire”;
- leitura do texto visível da página;
- envio para backend local;
- retorno do relatório.

### Limite importante

A extensão não deve tentar burlar login, captcha, bloqueio, rate limit ou controles de plataforma.
