# Estrutura de pastas

## Estrutura recomendada para o MVP

```text
sotuhire/
├── app.py
├── .env.example
├── README.md
├── LICENSE
├── modules/
│   ├── __init__.py
│   ├── cv_parser.py
│   ├── ats_analyzer.py
│   ├── ai_analyzer.py
│   ├── prompts.py
│   ├── schemas.py
│   ├── job_matcher.py
│   ├── business_rules.py
│   └── application_helper.py
├── tests/
│   ├── fixtures/
│   │   ├── sample_resume.txt
│   │   └── sample_job_description.txt
│   ├── test_ats_analyzer.py
│   ├── test_business_rules.py
│   ├── test_job_matcher.py
│   └── test_schemas.py
├── data/
│   └── .gitkeep
├── outputs/
│   └── .gitkeep
└── docs/
    ├── 00-audit/
    ├── 01-product/
    ├── 02-architecture/
    ├── 03-business-rules/
    ├── 04-ai/
    ├── 05-data-sources/
    ├── 06-engineering/
    ├── 07-development/
    └── requirements/
```

## Responsabilidade de cada arquivo

### `app.py`

Controla a interface Streamlit. Deve ser fino e fácil de ler.

### `cv_parser.py`

Extrai texto de currículos. No MVP, começa com PDF usando PyMuPDF. Futuramente pode suportar DOCX.

### `ats_analyzer.py`

Verifica sinais básicos de compatibilidade ATS:

- texto extraível;
- seções reconhecíveis;
- excesso de símbolos;
- possível uso de imagens;
- comprimento mínimo;
- presença de links úteis.

### `ai_analyzer.py`

Integra com Gemini, OpenAI ou outro modelo. A UI não deve conhecer detalhes da API.

### `prompts.py`

Guarda prompts em constantes/funções. Isso evita prompt perdido no meio do código.

### `schemas.py`

Define modelos Pydantic para entrada e saída.

### `job_matcher.py`

Combina análise da IA com regras determinísticas.

### `business_rules.py`

Centraliza termos e regras de negócio.

### `application_helper.py`

Gera mensagens de candidatura, respostas curtas e textos de abordagem.

## Pastas que não devem ser versionadas

A pasta `data/` pode existir, mas currículos reais não devem ir para o GitHub.

Use `.gitignore` para impedir:

```text
/data/resumes/
/data/private/
/outputs/private/
*.pdf
*.docx
.env
```

## Evolução futura

Quando o projeto crescer, pode virar:

```text
sotuhire/
├── src/sotuhire/
│   ├── domain/
│   ├── services/
│   ├── infrastructure/
│   └── ui/
```

Mas isso só deve acontecer quando a estrutura simples começar a doer de verdade.


## Estrutura futura para fontes

```text
modules/
├── sources/
│   ├── __init__.py
│   ├── base.py
│   ├── manual_source.py
│   ├── public_page_source.py
│   ├── normalizer.py
│   ├── deduplication.py
│   └── errors.py
```

## Estrutura futura para CI

```text
.github/
└── workflows/
    └── ci.yml
```

## Configuração Python

```text
pyproject.toml
```

Centraliza:

- metadados do projeto;
- configuração do pytest;
- configuração do Ruff.

---

# Estrutura expandida sugerida

```text
modules/
├── ai/
│   ├── provider.py
│   ├── gemini_provider.py
│   ├── openrouter_provider.py
│   └── prompt_registry.py
├── core/
│   ├── schemas.py
│   └── scoring.py
├── search_intelligence/
│   ├── query_generator.py
│   ├── source_ranker.py
│   ├── post_detector.py
│   └── source_registry.py
├── sources/
│   ├── base.py
│   ├── registry.py
│   ├── gupy.py
│   ├── infojobs.py
│   ├── indeed.py
│   ├── ciee.py
│   ├── inhire.py
│   ├── linkedin_manual.py
│   └── remotar.py
├── profile/
│   ├── linkedin_export_parser.py
│   ├── profile_score.py
│   └── lattes_parser.py
├── portfolio/
│   ├── github_analyzer.py
│   ├── portfolio_score.py
│   └── file_sampler.py
├── rag/
│   ├── ingestion.py
│   ├── retriever.py
│   └── memory_store.py
├── tracker/
│   ├── kanban.py
│   └── follow_up.py
└── alerts/
    └── notifier.py
```

A regra é manter cada módulo pequeno, testável e sem acoplamento com a UI.
