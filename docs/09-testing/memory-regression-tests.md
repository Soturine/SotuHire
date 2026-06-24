# Testes de regressão da memória

A suíte da v0.8.0 valida a memória local sem depender de Gemini, rede ou dados pessoais reais.

## Cobertura

- CRUD e limpeza do store;
- busca por keyword;
- boosts por tags, tipo e recência;
- conversão de resultados em evidências;
- análise local com e sem memória;
- bloqueio de contexto para Gemini sem opt-in;
- envio de contexto relevante com opt-in;
- feedback convertido em memória;
- construção e completude do perfil;
- preferências inferidas;
- export/import;
- Search Intelligence e Hidden Jobs Radar personalizados;
- UI avançada e tracker.

## Fixtures

Fixtures fictícias ficam em `tests/fixtures/memory/`. Exemplos portáteis ficam em
`examples/memory/`. Nenhum arquivo deve conter dados pessoais reais.

## Comandos

```bash
python -m pytest -q
npx --yes pyright
ruff check .
ruff format . --check
mkdocs build --strict
```
