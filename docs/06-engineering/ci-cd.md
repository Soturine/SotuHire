# CI/CD

## Workflows

| Workflow | Responsabilidade |
| --- | --- |
| `ci.yml` | matriz Python, qualidade, cobertura, frontend e pacote da extensão |
| `docs.yml` | build estrito e publicação da documentação no GitHub Pages |
| `codeql.yml` | análise estática Python e JavaScript/TypeScript |
| Dependabot | atualizações semanais de pip, npm e GitHub Actions |

## Matriz Python

A suíte pytest com mocks/fixtures roda em:

- Ubuntu + Python 3.11;
- Ubuntu + Python 3.12;
- Windows + Python 3.11;
- Windows + Python 3.12.

Um job Ubuntu/Python 3.12 executa adicionalmente Ruff, format check, compileall, Pyright, validators, dry-run da migração, data health, clean install e cobertura. O baseline local inicial é 86%; o relatório remoto é publicado como artefato, sem threshold arbitrário antes de comparar ambientes de forma estável.

## Frontend

O job frontend executa:

```bash
npm ci
npm run test:unit
npm run lint
npm run typecheck
npm run build
npx playwright test tests/e2e/smoke.spec.ts tests/e2e/data-reliability.spec.ts --project=chromium
```

Vitest/Testing Library/MSW cobrem contratos rápidos; Playwright valida o navegador. O E2E usa dados de demonstração e APIs mockadas, sem provider externo.

## Extensão

`scripts/package_extension.py` valida Manifest V3, arquivos obrigatórios e padrões de segredo antes de criar o ZIP. O artefato é enviado pelo workflow para inspeção, não publicado automaticamente como release.

## Segurança e supply chain

- secret scan falha se uma credencial com padrão conhecido estiver rastreada;
- CodeQL analisa Python e JavaScript/TypeScript;
- Dependabot propõe atualizações pequenas e revisáveis;
- `npm audit` gera relatório e não bloqueia sozinho sem triagem;
- chamadas reais de IA e scraping de sites reais não rodam no CI;
- nenhum secret é necessário no workflow padrão.

## Política de publicação

1. validar a árvore local e os artefatos;
2. enviar commits à `main` sem force-push;
3. aguardar todos os checks remotos obrigatórios;
4. criar a tag anotada somente no commit verde;
5. criar GitHub Release com notas reais;
6. anexar somente ZIPs já escaneados e sem dados pessoais.

Falha de audit, CodeQL ou dependência deve ser analisada; falso positivo documentado não deve ser ocultado nem tratado automaticamente como vulnerabilidade explorável.
