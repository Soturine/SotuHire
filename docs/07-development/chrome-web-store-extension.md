# Publicação da extensão na Chrome Web Store

## Instalação em modo desenvolvedor

1. Abra `chrome://extensions`.
2. Ative **Modo do desenvolvedor**.
3. Clique em **Carregar sem compactação**.
4. Selecione `browser-extension/`.
5. Confirme no popup a versão do manifesto e execute o diagnóstico de compatibilidade.
6. Abra um repositório público do GitHub e confirme o botão **SotuHire Insight**.

## Gerar o ZIP

```bash
python scripts/package_extension.py
```

O script valida:

- Manifest V3 e versão;
- permissões e host permissions conhecidos;
- ícones 16, 48 e 128;
- arquivos executáveis, incluindo `queue_runtime.js`;
- ausência de `.env`, chave privada e padrões Gemini/OpenAI/GitHub;
- exclusão de testes, documentação e materiais da listagem.

O nome segue `dist/sotuhire-extension-v{manifest_version}.zip`. A versão atual do manifesto gera
`dist/sotuhire-extension-v0.9.3.zip`.

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

Esses arquivos não entram no ZIP executável. Revise textos, política, screenshots e instruções de
teste a cada mudança de permissão, provider, storage ou coleta.

## Permissões

| Permissão/host | Justificativa |
| --- | --- |
| `activeTab` | captura somente a aba atual após clique explícito |
| `scripting` | executa o extrator assistivo na aba selecionada |
| `storage` | preferências, lote e fila offline; nunca `chrome.storage.sync` para segredo |
| `127.0.0.1:8765` | Local Companion |
| `127.0.0.1:8787` | API local do SotuHire |
| `github.com` e `api.github.com` | botão contextual e sinais públicos |
| Gemini/OpenAI | catálogo e análise quando a pessoa escolhe provider próprio |

Não há `<all_urls>`, cookies, histórico, downloads, `webRequest` ou acesso a headers autenticados.

## Chaves e privacidade

A chave configurada no app nunca chega à extensão. Uma chave própria Gemini/OpenAI:

- usa `chrome.storage.session` por padrão;
- pode usar IndexedDB do service worker após consentimento explícito;
- não possui alegação de criptografia adicional;
- nunca entra em content script, página, Companion, fila, export ou screenshot;
- nunca usa `chrome.storage.sync`;
- pode ser removida no popup.

O conteúdo público só é enviado ao provider quando a pessoa inicia a análise. A extensão não
captura cookies, tokens, senhas, sessão, storage de terceiros ou dados privados ocultos. Não
automatiza login, CAPTCHA, candidatura ou inscrição.

## Estados visuais para a listagem

Gere as imagens determinísticas, sem rede nem chave:

```bash
python scripts/capture_extension_screenshots.py
```

Revise no mínimo:

- popup principal;
- Companion conectada e offline;
- captura de vaga, edital e GitHub;
- fila offline;
- configuração Gemini/OpenAI sem chave;
- contexto seguro e diagnóstico de compatibilidade;
- modal GitHub.

Não publique imagem com dado pessoal, segredo, erro inesperado ou texto cortado.

## Verificação antes de publicar

```bash
node --check browser-extension/queue_runtime.js
node --check browser-extension/github_injected.js
node --check browser-extension/project_analysis.js
node --check browser-extension/popup.js
node --check browser-extension/background.js
node --check browser-extension/content.js
pytest -q -k "extension or browser"
python scripts/package_extension.py
```

Depois, abra o ZIP e confirme que contém apenas os arquivos listados por `RUNTIME_FILES` em
`scripts/package_extension.py`.
