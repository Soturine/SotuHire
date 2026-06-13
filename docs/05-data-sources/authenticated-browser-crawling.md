# Authenticated Browser Crawling

## Objetivo

O modo `AUTHENTICATED_BROWSER` coleta vagas e publicações em uma fonte autenticada previamente
pela pessoa usuária. Ele conecta via CDP a um Chromium existente, abre abas próprias e mantém o
login sob controle humano.

## Preparar o navegador

Instale as dependências opcionais:

```bash
pip install -r requirements-scraping.txt
playwright install chromium
```

Inicie um perfil Chromium dedicado com CDP habilitado:

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir="$env:LOCALAPPDATA\SotuHire\chrome-profile"
```

Na primeira execução, faça login manualmente no navegador aberto. Nas próximas execuções, inicie
o mesmo perfil antes de clicar em **Coletar no navegador autenticado**.

## Executar no app

1. Abra **Modo avançado > Coletar vagas**.
2. Selecione **Navegador autenticado autorizado**.
3. Informe a URL inicial de uma lista de vagas, busca ou feed.
4. Configure limite de itens, páginas/rolagens e intervalo.
5. Registre a referência da autorização e confirme o uso autorizado.
6. Inicie a coleta.

O conector possui presets para:

- LinkedIn Jobs: encontra links de detalhes, navega páginas e coleta descrições;
- LinkedIn publicações: coleta cards visíveis e rola o feed/busca até o limite.

Para outra plataforma autorizada, configure `selectors` em `config/sources.toml`:

```toml
[[sources]]
name = "Authorized Platform"
type = "authenticated_browser"
url = "https://platform.example/jobs"
collection_mode = "AUTHENTICATED_BROWSER"
enabled = true
max_items = 100
max_pages = 10
delay_seconds = 2.0
browser_cdp_url = "http://127.0.0.1:9222"
authorized_use = true
authorization_reference = "Internal experiment approval"

[sources.selectors]
link = "a.job-link"
title = "h1"
content = "main .job-description"
next = "button.next-page"
```

Para coletar cards diretamente, use `item` e, opcionalmente, `item_link` no lugar de `link`.

## Comportamento

- usa somente o contexto Chromium já autenticado;
- abre e fecha apenas as abas criadas pelo crawler;
- deduplica oportunidades antes de salvar;
- interrompe ao detectar login, checkpoint ou CAPTCHA;
- não automatiza login, não tenta bypass e não envia candidatura.
