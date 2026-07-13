# Análise de GitHub e portfólio pela extensão

O analisador trabalha com perfis, repositórios, projetos e portfólios públicos. Ele não lê cookie,
token, sessão, `localStorage`, `sessionStorage`, header autenticado ou conteúdo privado oculto.

## Modos

### Independente

A extensão extrai sinais públicos e calcula um relatório determinístico no navegador. Opcionalmente,
a pessoa pode escolher Gemini ou OpenAI e uma chave própria.

- a chave usa `chrome.storage.session` por padrão;
- persistência em IndexedDB exige consentimento explícito;
- IndexedDB não implica criptografia adicional;
- o modelo escolhido é enviado à chamada real;
- catálogo oficial, cache e lista builtin têm origem/warning visíveis;
- chave e token nunca entram no payload do SotuHire;
- falha externa preserva relatório local e motivo do fallback.

### Conectado ao SotuHire

A extensão envia sinais públicos à API local. O SotuHire:

1. valida o payload;
2. consulta apenas contexto seguro necessário;
3. prioriza arquivos centrais;
4. analisa README, arquitetura e commits;
5. registra provider, modelo, prompt e fallback;
6. cria snapshots e salva relatório/evidências;
7. oferece candidatos revisáveis para o Perfil.

A chave configurada no app permanece no backend local.

## Botão e modal

Em repositórios, árvores, arquivos e perfis públicos, o script restrito a `github.com` injeta o
botão **SotuHire Insight**. A inserção usa ações do repositório e cabeçalho como fallback; um
`MutationObserver` reaplica o botão após navegação SPA.

O modal mostra score, grade, provider/modelo, stack, README, commits, arquitetura, profundidade,
manutenção, prontidão para recrutadores, pontos fortes, gaps, recomendações e evidências seguras.
Também permite copiar, exportar ou enviar a análise ao SotuHire.

O modo **Deep analysis** aumenta a amostra de sinais públicos, sem desbloquear conteúdo privado.

## Amostragem

Prioridade alta:

- `README.md`, `package.json`, `pyproject.toml`, `requirements.txt`;
- `Dockerfile`, compose e workflows;
- `src/`, `app/`, `modules/`, `tests/` e `docs/`.

Ignorados:

- `node_modules`, `dist`, `build`, `.venv` e `__pycache__`;
- imagens, binários, compactados e locks;
- arquivos acima do limite local.

A extensão pode enriquecer a amostra pela API pública do GitHub, sem token e com
`credentials: omit`. Rate limit ou falha preserva os sinais visíveis.

## Rastreabilidade

O relatório informa:

```txt
provider_requested
provider_used
model_requested
model_used
prompt_id
prompt_version
analysis_mode
fallback_used
fallback_reason
source_refs
evidence_used
needs_user_review
```

Scores determinísticos críticos não são substituídos cegamente pelo texto do provider. Evidências
para currículo continuam sugestões e não devem inventar experiência, impacto ou domínio técnico.

## Integração

```text
POST /capture/github-profile
POST /capture/github-repo
POST /capture/portfolio
POST /capture/project
POST /capture/repo-analysis
POST /capture/commit-analysis
```

No site, projetos salvos podem gerar candidatos com `source_ref`, comparar evidências com uma vaga
e participar do Career Context depois de revisão/confirmação.

## Validação

```bash
pytest -q tests/test_extension_ai_provider_runtime.py
pytest -q tests/test_extension_reliability_runtime.py
node --check browser-extension/background.js
node --check browser-extension/github_injected.js
python scripts/package_extension.py
```
