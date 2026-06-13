# Pipeline de Coleta de Oportunidades

## Fluxo

```text
URL ou fonte configurada
-> inspeção de acesso público
-> robots.txt
-> cache local
-> rate limit por domínio
-> fetch identificado
-> parsing HTML ou XML
-> ScrapedOpportunity
-> deduplicação
-> store local
-> JobPostingSchema
-> análise e tracker
```

Cada coleta parte de uma ação explícita. O cliente usa user-agent identificável, limita bytes, respeita `robots.txt` e registra somente conteúdo necessário para a oportunidade.

## Modos explícitos

`ScrapingSource.collection_mode` diferencia:

- `PUBLIC_SCRAPING`: cliente HTTP para páginas públicas e feeds;
- `MANUAL_URL`: coleta uma única URL e não segue links em massa;
- `USER_ASSISTED_CAPTURE`: processa somente o conteúdo visível da página atual fornecido pela pessoa usuária.

Uma captura assistida pode vir de uma página aberta em uma sessão própria já autenticada. Nesse modo, o SotuHire não faz requisição à plataforma, não lê cookies e não percorre outras páginas.

## Contratos

`ScrapingSource` descreve tipo, URL, limite, intervalo e seletores futuros. `ScrapedOpportunity` guarda origem, fatos detectados, descrição, hash e timestamp com timezone.

O `OpportunityStore` deduplica por URL normalizada, identidade semântica e `content_hash`. O normalizador converte a oportunidade para o mesmo `JobPostingSchema` usado por vagas coladas.

## Cache e falhas

Respostas públicas ficam em `data/scraping-cache` por seis horas. Uma fonte com erro retorna uma falha estruturada e não derruba o app. Dados em `data/` não são versionados.

## Limites

A pipeline não autentica em plataformas, não contorna captcha ou bloqueios e não envia candidaturas. Páginas autenticadas abertas pela pessoa usuária podem ser processadas somente via captura assistida da página atual. Fontes públicas compatíveis podem ser adicionadas pelo registry ou por `config/sources.toml`.
