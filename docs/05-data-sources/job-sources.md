# Fontes de vagas

## Estratégia

O SotuHire deve começar com entrada manual e evoluir para coleta controlada.

A ordem recomendada é:

1. descrição colada manualmente;
2. texto de post colado manualmente;
3. link de vaga salvo manualmente;
4. leitura de páginas públicas simples;
5. conectores específicos para fontes públicas;
6. Hidden Jobs Radar;
7. extensão assistiva;
8. crawlers mais estruturados, se fizer sentido.

## Fontes formais possíveis

Fontes que podem ser estudadas:

- Greenhouse;
- Lever;
- Ashby;
- Gupy;
- LinkedIn;
- Indeed Brasil;
- InfoJobs;
- CIEE;
- Companhia de Estágios;
- InHire;
- Vagas.com;
- Catho;
- Cia de Talentos;
- Nube;
- 99jobs;
- Eureca;
- Remotar;
- Programathor;
- Trabalha Brasil;
- BNE;
- sites de carreira de empresas;
- páginas de programas de estágio;
- murais de universidades;
- newsletters públicas;
- comunidades com entrada manual.

## Prioridade inicial

Para o MVP, não tente cobrir tudo.

Prioridade recomendada:

```text
1. entrada manual
2. páginas públicas simples
3. páginas de carreira de empresas específicas
4. Greenhouse/Lever/Ashby quando a URL pública for clara
5. Hidden Jobs Radar por texto colado
```

Na v1.8.0, o fluxo real de entrada esta documentado em
[`public-source-importers.md`](public-source-importers.md): texto, link publico simples, CSV, JSON,
upload com preview, historico persistente, deduplicacao local, merge visual e exportacao. O Radar de
Vagas com RSS/Atom publico fica em [`job-radar-public-feeds.md`](job-radar-public-feeds.md).


## Portais brasileiros

Os detalhes por portal estão em [`brazilian-job-portals.md`](brazilian-job-portals.md).

Resumo de abordagem:

- **LinkedIn**: manual/assistivo; não usar bot logado.
- **Gupy**: prioridade alta; começar com link e descrição colada; conector planejado.
- **InfoJobs/Indeed**: agregadores; exigem deduplicação forte.
- **CIEE/Companhia de Estágios**: prioridade alta para estágio, aprendiz e trainee.
- **InHire**: fonte dinâmica; começar manual e avaliar caso a caso.
- **Vagas.com/Catho**: úteis, mas com conectores planejados e avaliação de termos.
- **Cia de Talentos/Nube/99jobs/Eureca**: categoria de programas de entrada.

## Campos normalizados

Toda vaga coletada deve virar um objeto comum:

```json
{
  "id": "hash-or-uuid",
  "title": "Estágio em Dados",
  "company": "Empresa X",
  "location": "São Paulo, SP",
  "work_model": "hybrid",
  "seniority": "internship",
  "source": "company_page",
  "source_url": "https://...",
  "application_url": "https://...",
  "description": "Texto completo da vaga",
  "requirements": ["Python", "SQL"],
  "nice_to_have": ["Power BI"],
  "salary_min": null,
  "salary_max": null,
  "currency": "BRL",
  "published_at": null,
  "collected_at": "2026-06-12T03:00:00",
  "content_hash": "sha256..."
}
```

## Deduplicação

A mesma vaga pode aparecer em várias fontes. O sistema deve comparar:

- URL;
- título;
- empresa;
- local;
- senioridade;
- trecho da descrição;
- hash do conteúdo.

## Scraping

Sim, o SotuHire pode fazer scraping, mas com limites claros.

Regras:

- respeitar `robots.txt` quando aplicável;
- aplicar rate limit;
- usar cache;
- não burlar login;
- não burlar CAPTCHA;
- não usar proxies para contornar bloqueio;
- não coletar dados pessoais em massa;
- não acessar áreas privadas;
- não fazer auto-apply;
- não enviar mensagens automáticas.

## Ferramentas possíveis

### Requests/HTTPX + BeautifulSoup

Usar para páginas HTML simples.

Vantagens:

- simples;
- rápido;
- fácil de testar;
- bom para MVP.

### Playwright

Usar quando a página pública depende de JavaScript.

Vantagens:

- renderiza páginas dinâmicas;
- permite testes E2E;
- útil para extensão/validação visual.

Desvantagens:

- mais pesado;
- mais lento;
- aumenta risco de overengineering;
- deve ser usado com cuidado.

### Scrapy

Usar quando houver múltiplas páginas, paginação, pipelines e necessidade de controle fino.

Vantagens:

- estrutura própria para crawlers;
- settings para `robots.txt`;
- throttling;
- pipelines;
- logs.

Desvantagens:

- mais complexo;
- não é necessário no MVP 1;
- pode virar overengineering se usado cedo demais.

## LinkedIn

LinkedIn deve ser tratado com cuidado.

Permitido no SotuHire:

- colar descrição da vaga;
- colar texto do post;
- salvar link manualmente;
- extensão local que lê o conteúdo aberto pelo usuário, se houver cuidado e transparência.

Evitar:

- bot logado;
- scraping de feed;
- scraping de perfis;
- download de contatos;
- envio automático de mensagem;
- auto-apply.

## Critérios para adicionar uma fonte

Uma fonte só deve ser adicionada quando:

- há valor real para o usuário;
- o acesso é público ou permitido;
- a fonte tem estrutura estável;
- o conector é testável;
- existe rate limit;
- existe log de coleta;
- não exige bypass;
- não coleta dados desnecessários.

## Métricas de coleta

O sistema deve registrar:

- quantidade de vagas coletadas;
- quantidade de vagas válidas;
- quantidade de duplicatas;
- quantidade de erros;
- tempo de execução;
- fontes ativas;
- última coleta por fonte.

## Próximo passo técnico

Criar:

```text
modules/sources/
├── base.py
├── manual_source.py
├── public_page_source.py
├── normalizer.py
└── deduplication.py
```
