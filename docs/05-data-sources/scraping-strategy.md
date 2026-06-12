# Estratégia de scraping responsável

## Resposta direta

Sim: o SotuHire pode ter scraping.

Mas o scraping do SotuHire deve ser tratado como **coleta responsável de oportunidades públicas**, não como automação agressiva, invasiva ou de candidatura em massa.

O objetivo do módulo de scraping é encontrar e normalizar oportunidades para análise posterior. Ele não deve aplicar automaticamente, não deve burlar login, não deve capturar dados pessoais desnecessários e não deve tentar contornar bloqueios.

## Por que incluir scraping

O scraping faz sentido porque muitas vagas aparecem fora de APIs organizadas:

- páginas públicas de carreira;
- sistemas de recrutamento com páginas abertas;
- posts públicos;
- newsletters;
- páginas simples de empresas;
- listagens de programas de estágio;
- comunidades com oportunidades copiadas pelo usuário;
- sites de vagas com HTML acessível.

Sem algum nível de coleta, o usuário continuaria dependendo de busca manual. O diferencial do SotuHire é transformar essas oportunidades em dados estruturados e comparáveis.

## O que é permitido no escopo do projeto

O projeto pode implementar:

- leitura de páginas públicas;
- coleta de título, empresa, local, modalidade e descrição;
- normalização de vagas em um schema comum;
- deduplicação;
- cache local;
- rate limit;
- logs de fonte;
- ingestão manual de links;
- ingestão manual de texto colado;
- leitura de feeds, quando disponíveis;
- integração com APIs oficiais, quando disponíveis.

## O que fica fora do escopo

O SotuHire não deve implementar:

- bypass de CAPTCHA;
- bypass de login;
- uso de cookies privados para raspagem em massa;
- simulação de comportamento humano para escapar de bloqueios;
- rotação de proxies para contornar rate limits;
- coleta massiva de perfis pessoais;
- envio automático de mensagens;
- candidatura automática em massa;
- scraping de áreas privadas;
- coleta de dados além do necessário para avaliar uma vaga.

## Camadas de coleta

A arquitetura deve separar os níveis de fonte.

### Nível 0 — Manual

É o mais seguro e deve vir primeiro.

Entradas:

- texto de vaga colado;
- texto de post colado;
- link salvo manualmente;
- arquivo com lista de vagas;
- CSV/JSON importado.

Vantagens:

- baixo risco;
- fácil de testar;
- não depende de bloqueios;
- útil desde o MVP.

### Nível 1 — Páginas públicas simples

Coleta com `requests` ou `httpx` + `BeautifulSoup`.

Usar quando:

- a página é pública;
- o HTML já vem renderizado;
- não precisa de login;
- não há interação complexa;
- a fonte permite acesso razoável.

Exemplos de uso:

- páginas de carreira estáticas;
- listagens públicas simples;
- blogs de vagas;
- páginas de programas de estágio;
- newsletters publicadas em HTML.

### Nível 2 — Páginas públicas dinâmicas

Coleta com Playwright.

Usar quando:

- o conteúdo é público;
- a página depende de JavaScript;
- o HTML inicial não contém a vaga;
- não há login obrigatório;
- a coleta respeita limites de acesso.

Playwright deve ser exceção, não padrão. Ele é mais pesado, mais lento e mais fácil de usar de forma errada.

### Nível 3 — Crawlers estruturados

Coleta com Scrapy.

Usar quando:

- existem várias páginas da mesma fonte;
- há paginação;
- é necessário agendar crawls;
- é importante controlar delays, pipelines, cache e logs;
- a fonte é permitida e estável.

Scrapy é útil para fontes públicas, mas não deve ser usado para “forçar” plataformas fechadas.

## Fonte normalizada

Toda oportunidade coletada deve virar um objeto comum.

```json
{
  "source_name": "Greenhouse",
  "source_type": "job_board",
  "url": "https://example.com/job/123",
  "title": "Estágio em Dados",
  "company": "Empresa Exemplo",
  "location": "Brasil",
  "work_model": "remote",
  "seniority": "internship",
  "description": "Texto completo da vaga",
  "requirements": ["Python", "SQL", "Excel"],
  "nice_to_have": ["Power BI"],
  "salary": null,
  "published_at": null,
  "collected_at": "2026-06-12T03:00:00",
  "raw_html_hash": "sha256...",
  "content_hash": "sha256..."
}
```

## Deduplicação

A mesma vaga pode aparecer em várias fontes. O SotuHire deve evitar duplicatas com uma combinação de:

- URL canônica;
- título normalizado;
- empresa normalizada;
- localidade;
- hash da descrição;
- similaridade de texto.

Regras simples para o MVP:

```text
duplicata forte = mesma URL
duplicata provável = mesmo título + empresa + local
duplicata semântica = descrição muito parecida
```

## Rate limit

Cada conector deve ter limites próprios.

Exemplo:

```python
SOURCE_LIMITS = {
    "greenhouse": {"delay_seconds": 2, "max_pages_per_run": 20},
    "lever": {"delay_seconds": 2, "max_pages_per_run": 20},
    "generic_company_page": {"delay_seconds": 5, "max_pages_per_run": 10},
}
```

## Cache

O sistema deve cachear páginas ou resultados para evitar baixar a mesma coisa toda hora.

Pode salvar:

- URL;
- data da coleta;
- status HTTP;
- hash do conteúdo;
- conteúdo extraído;
- erro, se houver.

## Robots.txt

Quando aplicável, o scraper deve respeitar `robots.txt`.

Para Scrapy, isso deve ficar explícito:

```python
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
AUTOTHROTTLE_ENABLED = True
```

## User-Agent

Use um User-Agent identificável e honesto.

Exemplo:

```text
SotuHireBot/0.1 (+https://github.com/Soturine/SotuHire; contact: your-email@example.com)
```

Não use User-Agent falso fingindo ser navegador comum só para evitar bloqueio.

## Logs

Todo conector deve registrar:

- fonte;
- URL;
- horário;
- status;
- quantidade de vagas;
- erro;
- tempo de execução.

Isso ajuda no debug e também mostra maturidade técnica.

## Falhas esperadas

Scraping quebra. Isso deve ser assumido desde o começo.

Motivos comuns:

- HTML mudou;
- fonte bloqueou;
- campo desapareceu;
- página virou dinâmica;
- vaga expirou;
- URL redirecionou;
- rate limit;
- erro temporário.

Por isso, cada conector deve ser isolado e testável.

## Ordem recomendada

1. Entrada manual.
2. Parser de URL pública simples.
3. Conector para páginas de carreira simples.
4. Conectores para sistemas públicos de vagas.
5. Hidden Jobs Radar.
6. Playwright apenas onde necessário.
7. Scrapy apenas quando houver volume e estabilidade.

## Critério de pronto

O scraping do SotuHire está pronto quando:

- cada fonte tem módulo próprio;
- existe schema comum;
- há rate limit;
- há logs;
- há testes com HTML salvo em fixture;
- não depende de conta do usuário;
- não faz auto-apply;
- não coleta dados pessoais desnecessários.
