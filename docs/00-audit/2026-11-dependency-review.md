# Dependências, advisories e Dependabot — 2026-11

Revisão de 2026-11-14 sobre `main` `8ea37d7`. Faz parte da
[auditoria independente de 2026-11](2026-11-independent-assurance-audit.md).

## npm (`apps/web/package-lock.json`)

`npm audit` em `8ea37d7`: 19 advisories (1 crítica, 6 altas, 12 moderadas). O passo do CI era
`continue-on-error`, então nenhuma falhou um build.

| Pacote | Sev. | Via | Decisão |
| --- | --- | --- | --- |
| seroval ≤1.6.7 | crítica | `@tanstack/router-core` (runtime) | `npm audit fix` — corrigido |
| vite 8.2.0–8.2.2 (launch-editor, Windows) | alta | direta, dev server | corrigido |
| undici, browserslist, brace-expansion, source-map-js | alta | transitivas de build/dev | corrigidas |
| zod <4.6.6 | alta | direta (`zod` 3.x, formulários) e `@tanstack/router-plugin` (build) | `DEFER_WITH_RISK`: exige migrar para zod 4 com `@hookform/resolvers`; impacto é esgotamento de memória ao validar coleções enormes no navegador do próprio usuário |
| eslint, typescript-eslint, minimatch, @vitest/mocker… | moderada | tooling de lint/teste | `DEFER_WITH_RISK`: só ambiente de desenvolvimento |

Depois de `npm audit fix` (sem `--force`): 8 restantes (1 alta, 7 moderadas). Verificado no
lockfile novo: `npm ci`, Vitest 18/18, ESLint, `tsc`, `vite build`, Playwright Chromium completo.

Política nova no CI: `npm audit --audit-level=critical` bloqueia; um segundo passo reporta as altas
sem bloquear, e cada alta precisa de decisão nesta tabela.

## Python

Não há lockfile Python. O CI instala `.[dev]` do zero e resolve as versões mais recentes, então o
`pip-audit` do CI passa; um ambiente local criado antes, mas ainda válido pelos pisos do
`pyproject`, acumulou advisories (`pypdf 6.15.0` com 29, `starlette`, `urllib3`, `jinja2`, `pillow`
entre outros). Como `pypdf` parseia PDFs enviados pelo usuário, os pisos subiram:

- `pypdf>=6.21.4,<7.0.0`
- `python-dotenv>=1.2.2`

Pendente: lockfile ou constraints Python para builds reproduzíveis e auditoria do conjunto exato
entregue.

## PRs do Dependabot

Estado em 2026-11-14 (nenhuma foi mesclada nesta auditoria; a integração em `main` segue o fluxo
de PR do repositório):

| PR | Atualização | Decisão |
| --- | --- | --- |
| #56 | Ruff 0.16.1 → 0.17.3 | `UPDATE`: mesclar junto com `rev` do pre-commit, depois de rodar `ruff check`/`format` (regras novas podem mudar o diff) |
| #51, #52, #53 | CodeQL init/analyze/autobuild 4.35.3 → 4.38.3 | `GROUP`: as três precisam andar juntas; o novo grupo `codeql` substitui as três PRs |
| #49 | upload-artifact 7.0.1 → 7.0.2 | `MERGE` após CI verde |
| #34 | deploy-pages 5.0.0 → 5.0.1 | `MERGE` após CI verde |
| #14, #16, #17, #18 | tailwindcss, radix tabs/label, prettier (`apps/web`) | `SUPERSEDE`: em conflito com o lockfile novo; o grupo `web-minor-patch` reabre de forma consolidada |
| #15 | globals 15 → 17 (major) | `DEFER`: avaliar com a configuração do ESLint |

PRs fechadas sem merge (#37–#48, #50, #54, #55) são versões intermediárias do mesmo Ruff/CodeQL
superadas pelas seguintes; não reabrir.

Causa de fundo: com `open-pull-requests-limit: 5`, as cinco PRs npm de 2026-08-10 bloquearam
qualquer atualização npm de versão posterior. `.github/dependabot.yml` agora agrupa CodeQL e
atualizações minor/patch por ecossistema.

## SBOM

`scripts/build_sbom.py` passou a inventariar todos os pacotes do lockfile npm e o fechamento
transitivo Python do ambiente, com arestas de dependência e propriedades declarando a fonte de
cada parte. `scripts/verify_sbom.py` falha se o arquivo faltar, se a versão divergir do
`pyproject`, se faltar pacote do lockfile ou se uma dependência obrigatória de runtime não estiver
instalada; extras opcionais ausentes ficam listados em `sotuhire:sbom:python-not-installed`.
