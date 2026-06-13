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
- `AUTHENTICATED_BROWSER`: navega uma fonte autorizada usando um Chromium já autenticado e conectado via CDP.

Uma captura assistida pode vir de uma página aberta em uma sessão própria já autenticada. Nesse modo, o SotuHire não faz requisição à plataforma, não lê cookies e não percorre outras páginas.

No modo autenticado, o Playwright conecta ao contexto existente sem receber senha ou automatizar
login. O crawler abre abas próprias, coleta cards ou links, percorre páginas/rolagens até os limites
configurados, normaliza os resultados e fecha somente as abas que criou.

## Contratos

`ScrapingSource` descreve tipo, URL, limite, intervalo e seletores futuros. `ScrapedOpportunity` guarda origem, fatos detectados, descrição, hash e timestamp com timezone.

O `OpportunityStore` deduplica por URL normalizada, identidade semântica e `content_hash`. O normalizador converte a oportunidade para o mesmo `JobPostingSchema` usado por vagas coladas.

## Cache e falhas

Respostas públicas ficam em `data/scraping-cache` por seis horas. Uma fonte com erro retorna uma falha estruturada e não derruba o app. Dados em `data/` não são versionados.

## Limites

A pipeline não automatiza login, não contorna CAPTCHA/checkpoints e não envia candidaturas. A coleta autenticada exige confirmação, permite registrar a referência de autorização e aplica limites de itens, páginas/rolagens e intervalo. Fontes públicas ou autenticadas autorizadas podem ser adicionadas pelo registry ou por `config/sources.toml`.
