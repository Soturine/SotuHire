# Extension Profile Bridge

A Extension Profile Bridge conecta capturas da extensão assistiva, Local Companion API, Career Context Engine e Perfil Profissional Universal.

O objetivo é simples: uma captura ou projeto pode sugerir evidências candidatas, mas nada entra no Perfil sem revisão e confirmação da pessoa usuária.

## Fluxo

```text
Extensão captura vaga/projeto/página visível
  -> Local Companion salva captura, memória, tracker ou projeto
  -> FastAPI lê /api/v1/extension/*
  -> Career Context Engine considera sinais locais
  -> Site mostra candidatos revisáveis
  -> Usuário confirma itens selecionados
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

Os endpoints de `profile-candidates` apenas geram rascunhos locais. Eles retornam `ProfileItem` com `confirmed_by_user=false`, `source`, `source_ref`, `confidence` e evidência textual curta.

Os endpoints de `add-to-profile` exigem confirmação explícita e salvam somente os itens selecionados. Ao salvar, o Perfil marca os itens como confirmados pela pessoa usuária.

## Fontes

As fontes permitidas para candidatos são:

- `extension_capture`;
- `github_capture`;
- `portfolio_capture`;
- `browser_assisted_capture`.

Uma vaga capturada não vira habilidade profissional automaticamente. Ela gera sinais como objetivo, preferência ou keyword/gap a revisar. Projetos GitHub/portfólio podem gerar item de projeto, skill, produção técnica ou evidência acadêmica candidata, sempre com revisão humana.

## Relação com Lattes/Acadêmico

A v1.9.2 adiciona o fluxo Lattes no Perfil, separado da extensão. Ainda assim, o Career Context Engine passa a enxergar evidências acadêmicas confirmadas e candidatos acadêmicos vindos de GitHub/Portfólio ou extensão quando forem explicitamente revisados.

## Privacidade

- A extensão não recebe API key do app.
- O frontend não persiste API key do provider.
- A ponte não coleta cookies, tokens, sessão, headers ou storage de terceiros.
- A ponte não automatiza candidatura.
- Capturas e projetos são locais e revisáveis.
- O fluxo `/api/v1/sources/authenticated-browser/*` não faz parte desta ponte e permanece separado.

## Arquivos Principais

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
