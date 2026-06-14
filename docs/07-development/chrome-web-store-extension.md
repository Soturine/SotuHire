# Publicação da extensão na Chrome Web Store

## Instalação em modo desenvolvedor

1. Abra `chrome://extensions`.
2. Ative **Modo do desenvolvedor**.
3. Clique em **Carregar sem compactação**.
4. Selecione a pasta `browser-extension/`.
5. Abra um repositório público do GitHub e confirme o botão **SotuHire AI**.

## Gerar o ZIP

```bash
python scripts/package_extension.py
```

O script valida:

- Manifest V3 e versão;
- permissões mínimas conhecidas;
- content script restrito ao GitHub;
- ícones `16`, `48` e `128`;
- presença dos arquivos executáveis;
- ausência de `.env`, chaves reais e arquivos de teste no pacote.

O resultado fica em `dist/sotuhire-extension-v0.9.0.zip`.

## Arquivos da listagem

```text
browser-extension/store/
├── listing.md
├── privacy-policy.md
├── test-instructions.md
├── description-short.txt
├── description-full.md
├── screenshots/
└── promo-assets/
```

Use esses textos para preencher nome, descrição curta, descrição completa, categoria,
funcionalidades, política de privacidade e instruções de revisão.

## Permissões

| Permissão | Motivo |
| --- | --- |
| `activeTab` | Capturar somente a aba atual após ação explícita. |
| `scripting` | Executar o extrator assistivo pelo popup. |
| `storage` | Guardar preferências, lote temporário e chave Gemini standalone opcional. |
| `http://127.0.0.1:8765/*` | Conectar à Local Companion API. |
| `https://github.com/*` | Injetar o botão público do analisador GitHub. |
| Gemini opcional | Solicitada somente quando a pessoa usa o modo standalone com Gemini. |

Não há permissão para cookies, histórico, downloads, headers, `webRequest` ou todos os sites.

## Privacidade

A extensão não captura cookies, tokens, senhas, `localStorage`, `sessionStorage`, headers
autenticados ou dados privados ocultos. A chave do Gemini configurada no SotuHire nunca é enviada
à extensão. A chave standalone opcional permanece em `chrome.storage.local` e é usada somente
após ação explícita.

## Verificação antes de publicar

```bash
node --check browser-extension/github_injected.js
node --check browser-extension/project_analysis.js
node --check browser-extension/popup.js
node --check browser-extension/content.js
python -m pytest -q tests/test_extension_store_package.py tests/test_extension_no_secrets_in_package.py
python scripts/package_extension.py
```
