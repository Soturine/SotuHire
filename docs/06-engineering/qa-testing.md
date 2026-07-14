# QA e testes

## Objetivo

QA verifica contratos de negócio, confiabilidade de dados, integração entre módulos e segurança. A suíte padrão é determinística: usa fixtures, mocks e servidores locais, sem depender de provider de IA ou site externo.

## Camadas

| Camada | Ferramentas | Exemplos |
| --- | --- | --- |
| Unitária Python | pytest | identidade, parser, score, dedupe, schemas |
| Integração Python | pytest + TestClient | API, Perfil/Contexto, Tracker, Radar, extensão |
| Persistência | sqlite3 + diretórios temporários | migração, FK, snapshots, backup, restore, health |
| Runtime da extensão | Node harness + pytest | fila, retry, JSON-LD, fallback e segredo |
| Frontend unit/component | Vitest, React Testing Library, MSW | mappers, estados e cliente de dados |
| Frontend E2E | Playwright | Demo/API mock, painel de dados, responsividade |
| Documentação | MkDocs strict + geradores | links, nav, capabilities e prompts |

## Persistência e migração

Testar obrigatoriamente:

- dry-run não cria DB, backup ou temporário no diretório de dados;
- apply cria backup e preserva JSON/JSONL;
- importação é transacional e idempotente;
- IDs não duplicados são preservados;
- dedupe usa somente identidade forte ou conteúdo exato;
- corrupção é rejeitada explicitamente;
- schema metadata e migration history concordam;
- foreign keys e integrity check passam;
- health não altera banco pré-schema;
- restore valida checksum, versão, schema e SQLite antes de gravar.

## Snapshots e Tracker

- snapshot é content-addressed e imutável por trigger;
- conteúdo alterado gera novo hash/snapshot;
- entidade referenciada não pode ser apagada enquanto houver snapshot;
- Tracker mantém JobSnapshot, ResumeSnapshot e AnalysisSnapshot quando disponíveis;
- modo rápido continua aceitando cargo, empresa, URL e status;
- eventos de etapa são append-only e não são sobrescritos pela memória.

## Perfil, contexto e IA

- `confirmed_by_user`, confidence, sensitive e `source_ref` chegam ao Career Context;
- ATS/Tailor/Radar não promovem evidência não confirmada a fato seguro;
- provider/modelo/prompt/fallback são registrados;
- resultado de OpenAI não é rotulado como Gemini/fallback;
- AiRun rejeita material com aparência de segredo;
- testes externos são `external_ai`, opt-in e skipped sem variável temporária nova.

## Extensão

- handshake atual, antigo e incompatível;
- dedupe por URL canônica;
- retry/backoff/limite/estado;
- export/import sanitizado;
- JSON-LD `JobPosting` aninhado ou em `@graph`;
- fallback explícito;
- pacote sem segredo e com todos os arquivos do manifesto.

## Comandos

```bash
ruff check .
ruff format --check .
pytest
pytest --cov=modules --cov=apps/api --cov-report=term-missing
pyright
python -m compileall modules tests apps scripts
python scripts/validate_capabilities.py
python scripts/generate_integration_matrix.py --check
python scripts/generate_prompt_catalog.py --check
python scripts/migrate_local_data.py --dry-run
python scripts/check_data_health.py
python scripts/verify_clean_install.py
python scripts/package_extension.py
python scripts/run_ai_benchmark.py --suite mock
python scripts/run_ai_benchmark.py --suite golden --providers local
mkdocs build --strict
```

Frontend:

```bash
cd apps/web
npm ci
npm run test:unit
npm run lint
npm run typecheck
npm run build
npm run test:e2e
```

## Qualidade de IA

O CI padrão valida schemas golden, domínios/casos adversariais, prompt injection, métricas e regressão local sem chave. External AI é opt-in e usa exclusivamente variáveis temporárias permitidas. Relatórios não contêm inputs/outputs completos. Veja [benchmarking de IA](../09-testing/ai-benchmarking.md).

## Cobertura

A cobertura é medida, não presumida. O baseline local desta entrega é **86%**: 16.105 statements e 2.315 não cobertos, medidos com Python 3.12. O CI publica `coverage.json` como artefato e não impõe threshold arbitrário nesta primeira medição. A política seguinte deve impedir regressão e manter a evolução dos módulos críticos.

## Critério de fechamento

Uma release só pode declarar um comando verde quando ele foi executado. Skips e limitações devem aparecer nas release notes. Nenhum teste pode imprimir, salvar ou anexar chaves, cookies, tokens, dados pessoais ou storage da extensão.
