# SotuHire

> Assistente inteligente de carreira para análise de currículo, compatibilidade com vagas, otimização ATS, radar de oportunidades e apoio à candidatura — sem candidatura automática em massa.

O **SotuHire** é um projeto de portfólio focado em **IA aplicada, engenharia de software, regras de negócio, qualidade de código e produto real**. A ideia é ajudar uma pessoa candidata a decidir com mais clareza em quais vagas vale aplicar, quais pontos do currículo precisam melhorar e como escrever uma abordagem mais alinhada para recrutadores ou formulários.

O projeto começou como um “achador de vagas”, mas o escopo correto é mais forte e mais seguro: um **copiloto de carreira**. Ele não deve ser um bot de spam que entra em plataformas e se candidata sozinho. Ele deve buscar, organizar, analisar, explicar, ranquear e preparar a candidatura para revisão humana.

## Problema

Buscar vaga manualmente é cansativo porque muitas oportunidades são ruins para o perfil do candidato:

- pedem senioridade incompatível;
- exigem experiência impossível para estágio/júnior;
- misturam requisitos obrigatórios e desejáveis;
- escondem dados importantes no texto;
- aparecem como posts informais, e não como anúncio oficial;
- exigem adaptar currículo, mensagem e palavras-chave para cada vaga.

O SotuHire tenta resolver isso com um fluxo claro:

1. o usuário envia o currículo;
2. cola uma descrição de vaga, link ou texto de post;
3. o sistema extrai informações importantes;
4. calcula compatibilidade;
5. explica o resultado;
6. sugere melhorias;
7. ajuda a preparar uma resposta personalizada.

## O que o SotuHire faz

No MVP inicial, o sistema deve receber um currículo em PDF e uma descrição de vaga colada manualmente. A saída esperada é uma análise estruturada contendo:

- score de match entre currículo e vaga;
- recomendação: aplicar, aplicar com cautela ou não aplicar;
- pontos fortes do candidato;
- gaps técnicos e de senioridade;
- palavras-chave ausentes ou pouco destacadas;
- análise ATS básica;
- sugestão de mensagem curta para recrutador;
- observações sobre riscos da vaga.

Em versões futuras, o projeto pode evoluir para:

- histórico de análises;
- dashboard de vagas;
- buscador de vagas públicas;
- radar de posts de recrutadores;
- extensão de navegador para analisar uma vaga aberta pelo usuário;
- relatórios de melhoria do currículo;
- alertas configuráveis.

## Princípios do projeto

O SotuHire deve ser desenvolvido com estes princípios:

- **MVP simples primeiro:** validar o núcleo antes de adicionar dashboard, banco, scrapers e extensão.
- **Clean Code:** funções pequenas, nomes claros e responsabilidades bem separadas.
- **SOLID sem exagero:** aplicar separação de responsabilidades, interfaces simples e baixo acoplamento, mas sem transformar o MVP em arquitetura corporativa pesada.
- **Regras de negócio explícitas:** filtros, pesos, cortes de senioridade e critérios de recomendação devem estar em arquivos próprios, não escondidos dentro da UI.
- **QA desde cedo:** testar lógica determinística com `pytest`, principalmente regras de negócio e classificação.
- **IA estruturada:** preferir JSON/schema para respostas de LLM, em vez de texto solto difícil de validar.
- **Privacidade:** currículo é dado sensível; não deve ser versionado, logado nem enviado para mais serviços do que o necessário.
- **Uso responsável de fontes:** evitar automação agressiva, scraping logado sem autorização, bypass de captcha ou candidatura automática em massa.

## Arquitetura inicial

A primeira versão deve ser simples:

```text
sotuhire/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── modules/
│   ├── cv_parser.py
│   ├── ats_analyzer.py
│   ├── ai_analyzer.py
│   ├── job_matcher.py
│   ├── business_rules.py
│   └── application_helper.py
├── tests/
│   ├── test_business_rules.py
│   ├── test_job_matcher.py
│   └── test_ats_analyzer.py
└── docs/
    ├── 00-audit/
    ├── 01-product/
    ├── 02-architecture/
    ├── 03-business-rules/
    ├── 04-ai/
    ├── 05-data-sources/
    ├── 06-engineering/
    └── 07-development/
```

## Documentação

A documentação completa está organizada em subdiretórios:

| Área | Documento |
|---|---|
| Auditoria | [docs/00-audit/documentation-audit.md](docs/00-audit/documentation-audit.md) |
| Produto | [docs/01-product/vision.md](docs/01-product/vision.md) |
| Escopo | [docs/01-product/mvp-scope.md](docs/01-product/mvp-scope.md) |
| Roadmap | [docs/01-product/roadmap.md](docs/01-product/roadmap.md) |
| Arquitetura | [docs/02-architecture/overview.md](docs/02-architecture/overview.md) |
| Fluxo de dados | [docs/02-architecture/data-flow.md](docs/02-architecture/data-flow.md) |
| Regras de match | [docs/03-business-rules/matching-rules.md](docs/03-business-rules/matching-rules.md) |
| ATS | [docs/03-business-rules/ats-rules.md](docs/03-business-rules/ats-rules.md) |
| IA e prompts | [docs/04-ai/prompting.md](docs/04-ai/prompting.md) |
| JSON/schema | [docs/04-ai/structured-output-schema.md](docs/04-ai/structured-output-schema.md) |
| Fontes de vagas | [docs/05-data-sources/job-sources.md](docs/05-data-sources/job-sources.md) |
| Radar de posts | [docs/05-data-sources/hidden-jobs-radar.md](docs/05-data-sources/hidden-jobs-radar.md) |
| Clean Code/SOLID | [docs/06-engineering/clean-code-solid.md](docs/06-engineering/clean-code-solid.md) |
| QA/Testes | [docs/06-engineering/qa-testing.md](docs/06-engineering/qa-testing.md) |
| Setup | [docs/07-development/setup.md](docs/07-development/setup.md) |

## Tecnologias sugeridas

Para o MVP:

- Python
- Streamlit
- PyMuPDF
- Gemini API ou OpenAI API
- Pydantic
- pytest
- python-dotenv
- SQLite em versão futura

Referências úteis:

- [Gemini API - Libraries](https://ai.google.dev/gemini-api/docs/libraries)
- [Gemini API - Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Streamlit - Secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [PyMuPDF - Text extraction](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)
- [pytest - Getting started](https://docs.pytest.org/en/stable/getting-started.html)
- [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)

## Status

Este repositório está em fase inicial de documentação e definição de arquitetura. O próximo passo recomendado é implementar o **MVP 1**: upload de currículo + descrição de vaga + análise estruturada.

## Licença

Este projeto está licenciado sob a licença Apache 2.0. Consulte o arquivo [LICENSE](LICENSE).
