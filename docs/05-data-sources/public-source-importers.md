# Importadores e fontes publicas seguras

Este documento descreve o escopo seguro da v1.7.0 para entrada de vagas. Ele complementa os guias de
fontes de dados sem alterar regras protegidas de compliance ou navegador autenticado.

## O que existe na v1.7.0

- importacao manual por texto;
- importacao de uma URL publica especifica;
- importacao CSV;
- importacao JSON;
- historico local de capturas/importacoes;
- deduplicacao local explicavel;
- Caixa de Entrada de Oportunidades;
- conexao com Vaga, Analise de Compatibilidade e Candidaturas/Kanban.

## O que nao existe

- crawler amplo;
- busca massiva;
- login automatico;
- coleta de cookies/tokens;
- bypass de CAPTCHA;
- auto-apply;
- automacao de conta em plataformas de terceiros.

Se uma pagina exige login, bloqueia leitura publica simples ou nao permite extrair texto, o SotuHire
deve orientar a pessoa a abrir a pagina manualmente e colar o texto da vaga.

## Formato CSV

```csv
cargo,empresa,link,local,descricao,fonte,status,observacoes
Analista de Dados,Empresa Exemplo,https://example.com/jobs/123,Remoto,"Python, SQL e dashboards",CSV Manual,nova,"vaga ficticia"
Desenvolvedor Backend,Tech Exemplo,https://example.com/jobs/456,Hibrido,"APIs, testes e bancos de dados",CSV Manual,nova,"vaga ficticia"
```

Campos tambem aceitos em ingles:

```txt
title, company, url, location, description, source, status, notes
```

## Formato JSON

```json
[
  {
    "cargo": "Analista de Dados",
    "empresa": "Empresa Exemplo",
    "link": "https://example.com/jobs/123",
    "local": "Remoto",
    "descricao": "Python, SQL e dashboards.",
    "fonte": "JSON Manual",
    "status": "nova",
    "observacoes": "vaga ficticia"
  }
]
```

## Deduplicacao

Critérios usados:

- URL normalizada;
- empresa + cargo;
- empresa + cargo + localidade;
- texto normalizado da descricao.

O sistema marca `possible_duplicate` e mantem o historico. A pessoa decide se ignora, arquiva ou
mantem separado.

## Fontes publicas planejadas

Cards no frontend mostram como roadmap:

- paginas de carreira abertas;
- APIs oficiais;
- feeds publicos;
- CSV/JSON recorrente.

Esses itens sao exibidos como futuro/experimental e requerem revisao manual antes de qualquer
automacao recorrente.
