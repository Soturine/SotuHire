# GitHub e Portfolio Analyzer

O **GitHub/Portfolio Analyzer** avalia se os projetos públicos do usuário ajudam ou atrapalham uma candidatura.

A inspiração técnica vem de ferramentas como [RepoLogs](https://github.com/VictoriaSCorreia/RepoLogs_GithubExtension), que analisam repositórios públicos com IA e selecionam arquivos relevantes em vez de enviar o repositório inteiro.

## Objetivo

Responder:

- Quais repositórios combinam com a vaga?
- Quais projetos devem aparecer no currículo?
- Qual projeto deve ser fixado no GitHub?
- O README está bom?
- Existem testes?
- Existe demo?
- A stack é visível?
- O projeto prova alguma habilidade da vaga?

## Fontes aceitas

- [GitHub](https://github.com/)
- [GitLab](https://gitlab.com/)
- [Bitbucket](https://bitbucket.org/)
- [Kaggle](https://www.kaggle.com/)
- [Hugging Face](https://huggingface.co/)
- [npm](https://www.npmjs.com/)
- [PyPI](https://pypi.org/)
- [Docker Hub](https://hub.docker.com/)
- [Vercel](https://vercel.com/)
- [Netlify](https://www.netlify.com/)
- [Dev.to](https://dev.to/)
- [Medium](https://medium.com/)
- [Behance](https://www.behance.net/)
- [Dribbble](https://dribbble.com/)
- portfólio pessoal.

## Arquitetura

```mermaid
flowchart TD
    A[URL do projeto ou usuário] --> B[Portfolio Source Detector]
    B --> C[Metadata Collector]
    C --> D[File Sampler]
    D --> E[Quality Rules]
    E --> F[RAG Context]
    F --> G[LLM Analysis]
    G --> H[Portfolio Score]
    H --> I[Recomendações]
```

## File sampling inteligente

Para GitHub, o sistema deve priorizar:

- README.md;
- pyproject.toml;
- package.json;
- requirements.txt;
- Dockerfile;
- docker-compose.yml;
- .github/workflows;
- src/ ou modules/;
- tests/;
- docs/;
- arquivos principais da stack.

Não deve enviar tudo para IA sem necessidade.

## Métricas

```json
{
  "portfolio_score": 82,
  "readme_score": 90,
  "tests_score": 70,
  "architecture_score": 78,
  "job_alignment_score": 86,
  "security_flags": [],
  "recommended_repositories": ["SotuHire", "SoturAI", "SotuRail"]
}
```

## Regras de avaliação

### README

- explica o problema;
- mostra instalação;
- mostra uso;
- tem screenshots/GIF;
- tem roadmap;
- tem stack;
- tem licença;
- tem status do projeto.

### Código

- estrutura modular;
- nomes claros;
- separação de responsabilidades;
- testes;
- lint/format;
- CI;
- tratamento de erro;
- ausência de secrets.

### Alinhamento com vaga

- projeto usa stack pedida;
- resolve problema parecido;
- mostra maturidade técnica;
- tem documentação suficiente para recrutador entender rápido.

## Relação com SotuAI e SotuRail

O SotuHire pode usar projetos como SotuAI e SotuRail como evidências de:

- autonomia técnica;
- construção de produto;
- automação;
- IA;
- dados;
- documentação;
- publicação de pacote;
- visão de roadmap;
- capacidade de manter projeto.

Não deve exagerar. Deve transformar evidências reais em linguagem de currículo.

Exemplo:

```text
Projeto SotuRail demonstra publicação e manutenção de pacote, documentação e visão de produto.
Projeto SoturAI demonstra interesse em IA aplicada, automação e análise adaptativa.
Projeto SotuHire demonstra arquitetura, produto, regras de negócio, QA e IA aplicada à carreira.
```

## Saída para currículo

O módulo pode sugerir bullets:

```text
- Desenvolvi um copiloto de carreira com Python, IA generativa, análise ATS, scraping responsável e arquitetura modular.
- Estruturei documentação técnica com MkDocs, regras de negócio, CI, Ruff e testes automatizados.
- Projetei módulos de match, perfil, portfólio, RAG, job tracker e alertas.
```

## Cuidados

- Não analisar repositórios privados sem permissão.
- Não expor secrets.
- Não afirmar qualidade sem evidência.
- Não inventar métricas de impacto.
- Não baixar conteúdo excessivo.
- Não avaliar pessoas; avaliar projetos e sinais técnicos.

# Atualização: GitHub Analyzer 2.0

A análise GitHub/Portfólio evoluiu na v0.11.0 de sinais visíveis e heurísticas simples para uma base de pipeline profundo no backend/site do SotuHire.

A referência conceitual é a abordagem de ferramentas como REPOLOGS: analisar metadados, árvore, arquivos relevantes, dependências e documentação, em vez de depender apenas do DOM da página aberta.

## Nova divisão de responsabilidades

### Extensão

A extensão deve:

- detectar URL;
- extrair owner/repo quando for GitHub;
- capturar metadados visíveis quando necessário;
- chamar Local Companion API;
- mostrar resumo;
- abrir relatório completo no site.

### Backend/site

O backend agora possui base para:

- chamar GitHub API;
- coletar metadados;
- obter árvore completa;
- montar directory tree;
- selecionar arquivos relevantes;
- ler conteúdo raw;
- criar grafo simples de dependências;
- montar contexto;
- chamar prompt estruturado;
- validar JSON;
- calcular scores;
- salvar evidências.

Implementação principal: `modules/github_analyzer/`.

O fluxo antigo de `modules/portfolio` continua como fallback quando a API falha ou quando a extensão envia apenas sinais capturados.

## Pipeline proposto

```mermaid
flowchart TD
    A[Repo URL] --> B[Owner/Repo Parser]
    B --> C[GitHub Metadata]
    C --> D[Full Tree]
    D --> E[Filtered Directory Tree]
    E --> F[Priority Sampler]
    F --> G[Raw Files]
    G --> H[Dependency Graph]
    H --> I[Context Builder]
    I --> J[GitHub Repo Prompt]
    J --> K[Pydantic]
    K --> L[Score Calculator]
    L --> M[Career Evidence]
```

## Priority sampler

Prioridade alta:

- README;
- package manifest;
- pyproject;
- requirements;
- lockfile apenas como sinal, não como conteúdo completo;
- Dockerfile;
- docker-compose;
- workflows;
- docs;
- tests;
- entrypoints;
- arquivos centrais por grafo de dependência.

Ignorar conteúdo de:

- node_modules;
- dist;
- build;
- venv;
- cache;
- imagens;
- binários;
- dumps;
- arquivos enormes;
- outputs gerados.

## Prompt

Usar `github_repo_analysis_v2` do [Prompt Catalog](../04-ai/prompt-catalog.md).

A análise deve retornar:

- qualidade técnica;
- valor para currículo;
- prontidão para recrutador;
- evidências por arquivo;
- skills demonstradas;
- bullets seguros;
- inconsistências;
- riscos de segurança;
- recomendações priorizadas;
- alinhamento com vaga.

## Scores finais

A IA retorna `dimension_scores` e reasoning.

O código calcula:

- Technical Quality Score;
- Portfolio Score;
- Resume Evidence Score;
- Recruiter Readiness Score;
- Job Alignment Score.

## Diferença estratégica

REPOLOGS responde principalmente:

```text
Este repositório é tecnicamente bom?
```

SotuHire deve responder:

```text
Este repositório ajuda essa pessoa a conseguir quais vagas?
Como ele prova competências?
Como citar no currículo sem exagerar?
O que falta para ficar mais forte para recrutadores?
```

## Critério de pronto

O módulo estará pronto quando:

- repo por URL gerar relatório completo;
- relatório citar arquivos como evidência;
- o score técnico não for confundido com score de carreira;
- o repo puder ser comparado com vaga;
- bullets de currículo forem seguros;
- recomendações forem priorizadas;
- dados forem salvos na Career Memory quando o usuário confirmar.

Documento de implementação: [v0.11.0 GitHub Analyzer 2.0](../07-development/v0.11.0-github-analyzer-2.md).
