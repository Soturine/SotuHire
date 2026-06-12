# Search Intelligence / Motor de Descoberta de Vagas

O **Search Intelligence** é o módulo responsável por transformar intenção de carreira em buscas concretas, rastreáveis e priorizadas.

Ele não substitui portais de vagas. Ele ajuda o usuário a descobrir onde procurar, como procurar, quais termos usar e quais fontes priorizar.

## Problema

A busca de vagas costuma ficar presa em poucos canais:

- LinkedIn;
- Gupy;
- Indeed;
- InfoJobs;
- recomendações genéricas;
- candidatura automática sem estratégia.

Isso gera saturação, baixa resposta e sensação de esforço sem direção.

## Proposta

O SotuHire deve gerar buscas inteligentes para:

- Google;
- Bing;
- DuckDuckGo;
- LinkedIn Posts, quando o usuário copiar/colar texto ou link;
- portais brasileiros;
- portais internacionais;
- ATS públicos;
- páginas de carreira;
- comunidades;
- newsletters;
- oportunidades escondidas em posts.

## Arquitetura

```mermaid
flowchart LR
    A[Perfil alvo do usuário] --> B[Query Generator]
    B --> C[Source Registry]
    C --> D[Source Ranker]
    D --> E[Queries por fonte]
    E --> F[Entrada manual, scraping público ou extensão assistiva]
    F --> G[Opportunity Normalizer]
    G --> H[Matcher + Rules]
    H --> I[Tracker + Alertas]
```

## Módulos sugeridos

```text
modules/search_intelligence/
├── __init__.py
├── query_generator.py
├── source_ranker.py
├── post_detector.py
├── source_registry.py
└── search_session.py
```

## Query Generator

O gerador deve receber parâmetros e devolver buscas prontas.

Entrada:

```json
{
  "role": "Data Analyst",
  "seniority": "junior",
  "modality": "remote",
  "country": "Brazil",
  "skills": ["SQL", "Python", "Power BI"],
  "language": ["pt-BR", "en-US"]
}
```

Saídas possíveis:

```text
"Data Analyst" "Remote" "Junior" "SQL" "Brazil"
"Analista de Dados" "Remoto" "Júnior" "SQL"
"Estágio Dados" "Remoto" "Python"
"Junior Data Analyst" "Remote" "Brazil"
site:linkedin.com/posts "Data Analyst" "Junior" "Remote"
site:gupy.io "Estágio" "Dados" "SQL"
site:greenhouse.io "Data Analyst" "Brazil" "Remote"
site:lever.co "Junior" "Python" "Remote"
site:inhire.app "júnior" "python"
site:ciee.org.br "estágio" "tecnologia"
```

## Templates de busca por intenção

### Estágio em tecnologia

```text
"estágio" "tecnologia" "remoto"
"estágio" "python" "dados"
"estágio" "desenvolvimento" "híbrido"
"programa de estágio" "engenharia da computação"
site:ciee.org.br "estágio" "tecnologia"
site:ciadeestagios.com.br "tecnologia" "estágio"
```

### Júnior em dados

```text
"analista de dados" "júnior" "SQL"
"data analyst" "junior" "remote" "Brazil"
"Power BI" "vaga aberta" "júnior"
"contratando" "analista de dados" "SQL"
```

### Dev júnior

```text
"desenvolvedor junior" "python" "remoto"
"React" "vaga aberta" "júnior"
"Java" "estamos contratando" "junior"
"backend" "júnior" "remoto" "Brasil"
```

### QA júnior

```text
"QA junior" "vaga aberta"
"analista de testes" "júnior" "remoto"
"quality assurance" "junior" "Brazil"
"contratando" "QA" "automação"
```

## Source Ranker

O ranqueador de fontes deve considerar:

- aderência ao perfil;
- foco em estágio/júnior;
- confiabilidade da fonte;
- risco de scraping;
- possibilidade de entrada manual;
- existência de páginas públicas;
- qualidade dos metadados;
- frequência de atualização;
- histórico de bons matches do usuário.

Exemplo:

```json
{
  "source": "MeuHome",
  "priority": "high",
  "best_for": ["remoto", "híbrido", "tecnologia", "dados", "estágio", "júnior"],
  "risk": "low",
  "mode": ["public_page", "manual_link", "scraping_public"],
  "notes": "Boa fonte para vagas remotas/híbridas com recorte tech."
}
```

## Segurança e ética

O Search Intelligence deve preferir:

- buscas públicas;
- links colados pelo usuário;
- textos copiados pelo usuário;
- APIs oficiais quando existirem;
- extensão assistiva com clique explícito;
- cache e rate limit.

Deve evitar:

- scraping logado do LinkedIn;
- automação de candidatura;
- envio automático de mensagens;
- coleta massiva de dados pessoais;
- burlar captcha, login, paywall ou bloqueio técnico.

Referência: [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement).

## Relação com RAG

O Search Intelligence pode alimentar a base RAG do usuário com:

- vagas salvas;
- descrições analisadas;
- posts úteis;
- mensagens enviadas;
- respostas de recrutadores;
- histórico de resultado por fonte.

Assim, o SotuHire aprende quais fontes e queries funcionam melhor para o perfil do usuário.

Ver também: [RAG Memory Architecture](../04-ai/rag-memory-architecture.md).
