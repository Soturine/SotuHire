# Fontes Alternativas de Vagas

Este documento lista fontes alternativas que o SotuHire deve conhecer além de LinkedIn, Gupy, InfoJobs e Indeed.

A ideia não é usar todas ao mesmo tempo. A ideia é manter um **catálogo de fontes** com prioridade, risco, modo de acesso e aderência ao perfil.

## Fontes de prioridade alta

| Fonte | Link | Melhor para | Modo sugerido | Observação |
|---|---|---|---|---|
| MeuHome | <https://www.meuhome.com.br/> | Remoto, híbrido, tech, dados, estágio, trainee | público/manual/scraping responsável | Boa fonte brasileira para vagas remotas e híbridas. |
| Remotar | <https://remotar.com.br/> | Remoto Brasil | público/manual | Simples e alinhado a trabalho remoto. |
| Trampos | <https://www.trampos.co/> | Tech, produto, dados, marketing, design | público/manual | Relevante para áreas digitais. |
| Remote.co | <https://remote.co/remote-jobs/> | Remoto internacional | público/manual | Bom para filtros por categoria. |
| Working Nomads | <https://www.workingnomads.com/jobs> | Remoto internacional | público/manual | Útil para vagas remotas globais. |
| NoDesk | <https://nodesk.co/remote-jobs/> | Remoto internacional | público/manual | Pode ajudar em vagas globais e filtros. |
| Wellfound | <https://wellfound.com/jobs> | Startups, tech, remoto | manual/experimental | Exige filtro forte por senioridade. |

## Fontes de prioridade média

| Fonte | Link | Melhor para | Risco/limite |
|---|---|---|---|
| Arc.dev | <https://arc.dev/> | Dev remoto/freela | tende a perfil mais experiente. |
| Contra | <https://contra.com/> | Freelance/contratos | menos foco em estágio. |
| Dribbble Jobs | <https://dribbble.com/jobs> | Design/produto | menos útil para dev/dados. |
| Remote100K | <https://remote100k.com/> | remoto alto salário | geralmente senioridade alta. |
| Vagara | <https://www.vagara.com.br/> | vagas BR/curadoria | avaliar aderência. |
| Elevarb | <https://www.elevarb.com/> | carreira com IA/mentoria | avaliar se é fonte, produto ou comunidade. |

## Fontes brasileiras já mapeadas

Ver também: [Brazilian Job Portals](./brazilian-job-portals.md).

- [LinkedIn](https://www.linkedin.com/jobs/)
- [Gupy](https://www.gupy.io/)
- [InfoJobs](https://www.infojobs.com.br/)
- [Indeed Brasil](https://br.indeed.com/)
- [CIEE](https://portal.ciee.org.br/)
- [Companhia de Estágios](https://www.ciadeestagios.com.br/)
- [InHire](https://inhire.app/)
- [Vagas.com](https://www.vagas.com.br/)
- [Catho](https://www.catho.com.br/)
- [Cia de Talentos](https://www.ciadetalentos.com.br/)
- [Nube](https://www.nube.com.br/)
- [99jobs](https://www.99jobs.com/)
- [Eureca](https://eureca.me/)
- [Trabalha Brasil](https://www.trabalhabrasil.com.br/)
- [BNE](https://www.bne.com.br/)

## Fontes técnicas e portais de portfólio

Estas fontes não são apenas vagas, mas sinais de presença profissional:

| Fonte | Link | Uso no SotuHire |
|---|---|---|
| GitHub | <https://github.com/> | análise de projetos, README, commits, testes, stack. |
| GitLab | <https://gitlab.com/> | análise de projetos públicos. |
| Bitbucket | <https://bitbucket.org/> | análise de projetos públicos. |
| Kaggle | <https://www.kaggle.com/> | portfólio de dados e notebooks. |
| Hugging Face | <https://huggingface.co/> | modelos, datasets, Spaces e demos de IA. |
| npm | <https://www.npmjs.com/> | pacotes JavaScript publicados. |
| PyPI | <https://pypi.org/> | pacotes Python publicados. |
| Docker Hub | <https://hub.docker.com/> | imagens e projetos containerizados. |
| Vercel | <https://vercel.com/> | demos front-end e full-stack. |
| Netlify | <https://www.netlify.com/> | demos front-end. |
| Dev.to | <https://dev.to/> | artigos técnicos. |
| Medium | <https://medium.com/> | artigos técnicos. |
| Behance | <https://www.behance.net/> | portfólio visual/design. |
| Dribbble | <https://dribbble.com/> | portfólio visual/design. |
| Notion | <https://www.notion.so/> | portfólio pessoal/documentação. |

## Modelo de cadastro de fonte

```json
{
  "name": "MeuHome",
  "url": "https://www.meuhome.com.br/",
  "category": "remote_jobs",
  "country": "BR",
  "priority": "high",
  "access_mode": ["manual", "public_page", "scraping_public"],
  "best_for": ["remote", "hybrid", "tech", "data", "internship", "junior"],
  "risk_level": "low",
  "connector_status": "planned"
}
```

## Critérios para virar conector

Uma fonte só deve virar conector quando:

- tiver páginas públicas úteis;
- tiver estrutura previsível;
- não exigir login para os dados necessários;
- não exigir burlar captcha;
- permitir uso responsável com rate limit;
- gerar valor claro para estágio/júnior/tech;
- puder ser testada com fixtures HTML.

## Não objetivos

- Não transformar o SotuHire em raspador agressivo.
- Não usar proxies para contornar bloqueios.
- Não copiar bases inteiras de portais.
- Não automatizar candidatura.

## Relação com Search Intelligence

O Search Intelligence usa este catálogo para sugerir onde buscar primeiro.

Exemplo:

```text
Perfil: Estágio em Dados, São Paulo, remoto/híbrido.
Prioridade: CIEE, Companhia de Estágios, Gupy, MeuHome, LinkedIn Posts, InfoJobs.
Menor prioridade: Remote100K, Arc.dev, Contra.
```
