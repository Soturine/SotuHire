# Extension Profile Bridge

A Extension Profile Bridge conecta capturas da extensao assistiva, Local Companion API,
Career Context Engine e Perfil Profissional Universal.

O objetivo e simples: uma captura ou projeto pode sugerir evidencias candidatas, mas nada entra no
Perfil sem revisao e confirmacao da pessoa usuaria.

## Fluxo

```text
Extensao captura vaga/projeto/pagina visivel
  -> Local Companion salva captura, memoria, tracker ou projeto
  -> FastAPI le /api/v1/extension/*
  -> Career Context Engine considera sinais locais
  -> Site mostra candidatos revisaveis
  -> Usuario confirma itens selecionados
  -> Perfil Universal salva itens confirmados
```

## Endpoints

```txt
GET  /api/v1/extension/context
POST /api/v1/extension/captures/{capture_id}/profile-candidates
POST /api/v1/extension/captures/{capture_id}/add-to-profile
POST /api/v1/extension/projects/{project_id}/profile-candidates
POST /api/v1/extension/projects/{project_id}/add-to-profile
```

Os endpoints de `profile-candidates` apenas geram rascunhos locais. Eles retornam `ProfileItem`
com `confirmed_by_user=false`, `source`, `source_ref`, `confidence` e evidencia textual curta.

Os endpoints de `add-to-profile` exigem confirmacao explicita e salvam somente os itens
selecionados. Ao salvar, o Perfil marca os itens como confirmados pela pessoa usuaria.

## Fontes

As fontes permitidas para candidatos sao:

- `extension_capture`;
- `github_capture`;
- `portfolio_capture`;
- `browser_assisted_capture`.

Uma vaga capturada nao vira habilidade profissional automaticamente. Ela gera sinais como objetivo,
preferencia ou keyword/gap a revisar. Projetos GitHub/portfolio podem gerar item de projeto e skills
candidatas, sempre com revisao humana.

## Privacidade

- A extensao nao recebe API key do app.
- O frontend nao persiste API key do provider.
- A ponte nao coleta cookies, tokens, sessao, headers ou storage de terceiros.
- A ponte nao automatiza candidatura.
- Capturas e projetos sao locais e revisaveis.
- O fluxo `/api/v1/sources/authenticated-browser/*` nao faz parte desta ponte e permanece separado.

## Arquivos principais

```txt
apps/api/routes/extension.py
apps/api/services/extension.py
apps/api/schemas/extension.py
apps/web/src/routes/sources.tsx
modules/context
modules/local_api
modules/profile
browser-extension/README.md
tests/test_api_extension_bridge.py
```
