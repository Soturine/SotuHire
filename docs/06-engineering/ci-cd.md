# CI/CD

## Objetivo

O SotuHire deve ter um pipeline simples de qualidade para mostrar maturidade de engenharia sem exagerar.

O CI inicial deve responder:

1. o código instala?
2. o lint passa?
3. a formatação está correta?
4. os testes passam?

## GitHub Actions

Workflow atual na v1.8.1:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r docs/requirements/requirements.txt

      - name: Ruff check
        run: ruff check .

      - name: Ruff format check
        run: ruff format . --check

      - name: Tests
        run: pytest -v

      - name: Package browser extension
        run: python scripts/package_extension.py

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: apps/web/package-lock.json

      - name: Install frontend dependencies
        working-directory: apps/web
        run: npm ci

      - name: Frontend lint/typecheck/build
        working-directory: apps/web
        run: |
          npm run lint
          npm run typecheck
          npm run build

      - name: Frontend smoke E2E
        working-directory: apps/web
        run: npx playwright test tests/e2e/smoke.spec.ts --project=chromium
```

## O que não colocar no CI agora

Evite no começo:

- deploy automático;
- Docker complexo;
- banco externo;
- testes E2E pesados fora do smoke;
- Playwright sem mocks controlados;
- scraping real em sites externos;
- chamadas reais para API de IA.

## Testes com IA no CI

Não usar Gemini/OpenAI real em CI de rotina.

Motivos:

- custo;
- instabilidade;
- rate limit;
- internet;
- segredo de API;
- variação de output.

Use fixtures e mocks.

## Testes de scraping no CI

Não bater em sites reais no CI.

Use HTML salvo em `tests/fixtures/`.

Exemplo:

```text
tests/fixtures/sources/company_page_sample.html
```

O teste deve validar o parser com HTML local.

## Política de merge

Antes de mergear:

```bash
ruff check .
ruff format . --check
pytest
cd apps/web
npm run lint
npm run typecheck
npm run build
```

## Futuro

Depois do MVP, pode adicionar:

- coverage;
- build de docs com MkDocs;
- checagem de links;
- pacote Docker;
- deploy manual de documentação;
- releases versionadas.
