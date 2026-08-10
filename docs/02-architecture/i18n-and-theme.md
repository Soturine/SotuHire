# Internacionalização e tema

O frontend web usa catálogo TypeScript tipado em `apps/web/src/lib/i18n`, com `pt-BR` e `en-US`. A preferência aceita `system`, detecta `navigator.languages`/`languagechange`, resolve formatos por `Intl` e atualiza `html.lang` imediatamente.

Tema aceita `system`, `light` e `dark`. `prefers-color-scheme` é observado em tempo real; a preferência fica em `localStorage` e `applyStoredAppearance()` é executado antes do React. O CSS não baixa fontes: usa pilha local/sistema.

A extensão mantém `{locale, theme}` em `chrome.storage.local`, nunca em sync, e oferece ajuda no popup. O conteúdo histórico ainda está sendo migrado por domínio; chaves novas não devem ser hardcoded.

Regras: enums e payloads de API não são traduzidos; datas/números usam locale; contraste, foco e zoom devem ser verificados nos dois temas.
