# Testes da extensão assistiva

## Cobertura automatizada

Os testes da extensão cobrem contratos estáticos e runtimes JavaScript executados pelo Node:

- Manifest V3, versão e permissões mínimas;
- pacote contendo somente arquivos de runtime;
- secret scan para padrões Gemini, OpenAI, GitHub e chave privada;
- payload Pydantic compatível com o content script;
- Local Companion restrita a localhost;
- handshake compatível para a extensão atual e warning para versão antiga;
- JSON-LD `JobPosting` aninhado, inclusive `@type` em URL completa;
- precedência de título, organização, localização e descrição estruturados;
- fila deduplicada por URL sem parâmetros de tracking;
- `retry_count`, backoff, `next_retry_at`, estado e limite de tentativas;
- export/import da fila sem campos ou valores com formato de segredo;
- rejeição de paths importados fora de `/capture/`;
- catálogo real e modelo selecionado exercitados no harness do service worker;
- chaves Gemini/OpenAI fora de content script, página e payload conectado;
- sessão como padrão e IndexedDB somente após consentimento;
- fallback local com provider/modelo/motivo explícitos;
- análise pública de GitHub em modos independente e conectado;
- snapshots de captura/análise e vínculo com Tracker;
- candidatos para Perfil sempre revisáveis.

As fixtures em `tests/fixtures/extension/` são fictícias, não contêm chaves e não dependem de
portais reais. Os harnesses principais são:

```txt
background_harness.js
queue_runtime_harness.js
content_jobposting_harness.js
```

## Executar

```bash
pytest -q -k "extension or browser"
```

Para o conjunto funcional de confiabilidade:

```bash
pytest -q tests/test_extension_reliability_runtime.py
```

## Sintaxe JavaScript

Valide sem executar rede:

```bash
node --check browser-extension/queue_runtime.js
node --check browser-extension/popup.js
node --check browser-extension/background.js
node --check browser-extension/content.js
node --check browser-extension/project_analysis.js
node --check browser-extension/github_injected.js
```

## Validação manual

1. Inicie `python -m modules.local_api.server`.
2. Carregue `browser-extension/` como extensão sem compactação.
3. Abra o diagnóstico e confirme versões, capabilities e ausência de warnings.
4. Capture uma vaga fictícia com JSON-LD e confirme `schema_org_jobposting` no payload.
5. Capture novamente com parâmetros de tracking diferentes e confirme dedupe.
6. Desligue a Companion, capture uma vaga e confira a pendência offline.
7. Tente retry antes e depois do backoff; confira contador, erro e estado.
8. Exporte e importe a fila; confirme que não há chave, token ou identidade duplicada.
9. Capture um edital e confira o snapshot e a revisão no site.
10. Analise um repositório público nos modos local, Gemini/OpenAI próprios e IA do SotuHire.
11. Confirme no trace o provider/modelo realmente usados e qualquer fallback.
12. Gere candidatos para o Perfil e confirme que começam não confirmados.
13. Remova uma chave própria e confirme ausência em sessão e IndexedDB.

Nunca use chave real em fixture, screenshot ou gravação Playwright. Testes externos são opt-in e
devem usar exclusivamente variáveis temporárias de ambiente.

## Screenshots determinísticos

`scripts/capture_extension_screenshots.py` prepara estados com dados fictícios para:

- popup principal, conectada e offline;
- vaga, edital, GitHub e lote;
- fila offline com retry;
- configuração Gemini e OpenAI sem chave;
- contexto seguro e diagnóstico de compatibilidade;
- modal de análise GitHub.

O script não consulta provider nem portal real. Revise visualmente cada arquivo antes de publicar.

## Empacotamento

```bash
python scripts/package_extension.py
```

O comando valida Manifest, permissões, ícones, `queue_runtime.js` e padrões de segredo antes de
gerar o ZIP. Confirme também o conteúdo do arquivo:

```bash
pytest -q tests/test_extension_store_package.py tests/test_extension_no_secrets_in_package.py
```
