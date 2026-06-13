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

---

# Scraping + Search Intelligence + Alertas

O scraping no SotuHire deve ser um meio, não o produto inteiro.

Fluxo correto:

```text
buscar fonte -> coletar com limite -> normalizar -> deduplicar -> ranquear -> analisar match -> alertar apenas se fizer sentido
```

## Ordem de preferência técnica

1. Entrada manual.
2. Link público colado.
3. Requests/HTTPX + BeautifulSoup em página simples.
4. Playwright para página pública dinâmica.
5. Scrapy para crawlers maiores.
6. Selenium apenas quando necessário.

## Inspiração prática

Projetos simples de scraping com Selenium e Telegram mostram valor rápido, mas o SotuHire deve adicionar:

- arquitetura modular;
- conectores por fonte;
- logs estruturados;
- cache;
- rate limit;
- testes;
- deduplicação;
- análise de match antes do alerta.

Referência: [AUTOMATED_JOBSEACRH_SCRAPER](https://github.com/VictoriaSCorreia/AUTOMATED_JOBSEACRH_SCRAPER).

## Complemento: extensão assistiva antes de scraping agressivo

Quando a fonte for sensível, a estratégia preferida é:

1. usuário abre a página manualmente;
2. extensão captura apenas a página atual com clique explícito;
3. SotuHire salva no tracker;
4. análise ocorre localmente;
5. nenhuma candidatura é enviada automaticamente.

Essa abordagem é mais segura do que tentar navegar em massa por plataformas logadas.

## Implementação pública da v0.7.0

A v0.7.0 implementa coleta automática após ação explícita da pessoa usuária:

```text
detectar URL -> validar acesso público -> consultar robots.txt -> cache/rate limit
-> coletar -> normalizar -> deduplicar -> analisar
```

O cliente limita o tamanho da resposta, usa user-agent identificável e registra o domínio coletado. O cache local evita downloads repetidos e o store mantém oportunidades sem duplicação.

URLs públicas de qualquer domínio podem ser testadas. Caminhos que exigem autenticação e fontes proibidas por `robots.txt` retornam erro claro, sem tentativa de bypass.

## Três modos de coleta

### PUBLIC_SCRAPING

Para páginas abertas, RSS/Atom, páginas públicas de carreira e boards públicos. Usa cache, rate limit, limite de itens, logs e regras por fonte.

### MANUAL_URL

A pessoa usuária cola uma URL específica. O conector coleta somente aquela página e não segue links em massa sem uma nova ação explícita.

### USER_ASSISTED_CAPTURE

A pessoa usuária abre manualmente uma vaga ou publicação no navegador e envia o conteúdo visível da página atual ao SotuHire. Isso permite processar uma oportunidade vista dentro de uma sessão própria autenticada sem entregar cookies, credenciais ou controle de navegação ao app.

Esse modo oferece ações explícitas para salvar a vaga atual, analisá-la e enviá-la ao tracker. Ele não percorre feeds autenticados, não burla CAPTCHA e não envia candidatura.

### AUTHENTICATED_BROWSER

Para fontes autorizadas, conecta via CDP a um Chromium já autenticado pela pessoa usuária. O modo
navega automaticamente por listas de vagas ou publicações, abre detalhes, rola páginas dinâmicas e
normaliza oportunidades até os limites configurados.

Cada execução exige confirmação de uso autorizado e pode registrar uma referência local da autorização. O
crawler não automatiza login, interrompe em CAPTCHA/checkpoint, não tenta ocultar a automação e
não executa candidatura. Consulte o guia
[Authenticated Browser Crawling](authenticated-browser-crawling.md).
