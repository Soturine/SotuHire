# Fontes de vagas

## Estratégia

O SotuHire deve começar com entrada manual. Só depois deve evoluir para coleta de oportunidades. Isso reduz risco técnico e mantém foco no núcleo do produto.

## Fontes formais futuras

Possíveis fontes:

- Gupy;
- Greenhouse;
- Lever;
- Ashby;
- Indeed;
- InfoJobs;
- Remotar;
- Programathor;
- sites de carreira de empresas;
- páginas públicas com vagas.

## Campos normalizados

Toda vaga coletada deve virar um objeto comum:

```json
{
  "title": "Estágio em Dados",
  "company": "Empresa X",
  "location": "Remoto - Brasil",
  "work_model": "Remoto",
  "seniority": "Estágio",
  "source": "Gupy",
  "url": "https://...",
  "description": "Texto completo da vaga",
  "published_at": "2026-06-12"
}
```

## Deduplicação

A mesma vaga pode aparecer em várias fontes. O sistema deve comparar:

- título;
- empresa;
- local;
- link;
- trecho da descrição.

## Cuidados com scraping

Scraping deve ser tratado com maturidade:

- respeitar `robots.txt` quando aplicável;
- não burlar login;
- não burlar captcha;
- não simular comportamento humano para escapar de bloqueios;
- não coletar dados pessoais desnecessários;
- aplicar rate limit;
- preferir APIs, feeds, páginas públicas e entrada manual.

## LinkedIn

LinkedIn deve ser tratado com cuidado. O SotuHire pode suportar:

- usuário colar texto da vaga;
- usuário colar texto de post;
- usuário colar link para registro manual;
- extensão lendo página aberta pelo próprio usuário, se for implementada com limites claros.

O projeto não deve começar com bot logado no LinkedIn, coleta agressiva, automação de candidatura ou tentativa de contornar controles da plataforma.

## Abordagem segura para MVPs

Ordem recomendada:

1. vaga colada manualmente;
2. importação de links públicos;
3. leitura de páginas públicas simples;
4. fontes com estrutura previsível;
5. dashboard;
6. extensão opcional.
