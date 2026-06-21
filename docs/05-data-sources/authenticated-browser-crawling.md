# Authenticated Browser Crawling

## Objetivo

O modo `AUTHENTICATED_BROWSER` coleta vagas e publicações em uma fonte autenticada previamente
pela pessoa usuária. Ele conecta via CDP a um Chromium existente, abre abas próprias e mantém o
login sob controle humano.

## Preparar o navegador

Instale as dependências opcionais:

```bash
pip install -r docs/requirements/requirements-scraping.txt
playwright install chromium
```

Na tela **Navegador autenticado autorizado**, clique em **Abrir navegador para login**. O SotuHire
localiza Chrome, Edge ou Chromium, abre um perfil persistente dedicado com CDP habilitado e mantém
esse perfil para as próximas execuções.

Faça login manualmente no navegador dedicado que abrir. Depois volte ao app, clique em
**Testar conexão do navegador** e inicie a coleta.

O Chrome que já estava aberto antes não serve automaticamente, pois uma instância comum não
expõe a porta CDP. Para iniciar manualmente, use:

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir="$env:LOCALAPPDATA\SotuHire\chrome-profile"
```

O botão do app executa o equivalente automaticamente e usa o perfil em
`%LOCALAPPDATA%\SotuHire\authenticated-browser-profile`.

## Executar no app

1. Abra **Modo avançado > Coletar vagas**.
2. Selecione **Navegador autenticado autorizado**.
3. Informe a URL inicial de uma lista de vagas, busca ou feed.
4. Clique em **Abrir navegador para login** e faça login manualmente no navegador aberto.
5. Clique em **Testar conexão do navegador**.
6. Configure limites, registre a referência da autorização e confirme o uso autorizado.
7. Inicie a coleta quando a tela mostrar **Conexão CDP pronta**.

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
