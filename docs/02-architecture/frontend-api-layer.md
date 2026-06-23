# Frontend API Layer

A camada FastAPI local em `apps/api` conecta o frontend moderno ao core Python sem mover regra
crítica para JavaScript. Na v1.4.0, ela também expõe configurações locais seguras de IA para a tela
**Configurações → IA e Providers**.

## Objetivo

- expor contratos HTTP versionados em `/api/v1`;
- manter Streamlit como modo legado/dev/local debug;
- manter Local Companion API como ponte da extensao assistiva;
- preparar Lovable, React, Vite ou Next.js para consumir endpoints reais;
- preservar privacidade local-first e anti-fabrication.

## Entrada

```powershell
python scripts/run_api.py
```

Fluxo web-first:

```powershell
.\start-sotuhire.ps1
```

OpenAPI:

```text
http://127.0.0.1:8787/openapi.json
http://127.0.0.1:8787/docs
```

## Camadas

```text
frontend moderno
    -> apps/api/routes
    -> apps/api/services
    -> modules/parsers, modules/ai, modules/matching, modules/ats,
       modules/resume_tailor, modules/github_analyzer, modules/tracker
    -> data local quando a pessoa confirma privacidade
```

`apps/api` deve ser uma camada fina. O core continua em `modules/`.

## CORS

O CORS e restrito por default. A lista inicial cobre desenvolvimento local e GitHub Pages:

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:8501`
- `http://127.0.0.1:8501`
- `https://soturine.github.io`

Use `SOTUHIRE_API_ALLOWED_ORIGINS` para alterar a lista.

## Diferenca para Local Companion API

| API | Porta padrao | Uso |
| --- | --- | --- |
| Frontend API Layer | `8787` | frontend moderno e contratos `/api/v1` |
| Local Companion API | `8765` | extensao assistiva e capturas do navegador |

As duas sao locais. A Frontend API usa FastAPI e OpenAPI. A Local Companion API continua usando
biblioteca padrao do Python e endpoints `/capture/*`.

## Endpoints `/api/v1`

- `GET /api/v1/health`
- `POST /api/v1/resume/extract`
- `POST /api/v1/job/extract`
- `POST /api/v1/match/analyze`
- `POST /api/v1/ats/analyze`
- `POST /api/v1/resume/tailor`
- `POST /api/v1/github/repo/analyze`
- `GET /api/v1/tracker/jobs`
- `POST /api/v1/tracker/jobs`
- `PATCH /api/v1/tracker/jobs/{id}`
- `GET /api/v1/tracker/metrics`
- `GET /api/v1/tracker/requirements`
- `GET /api/v1/tracker/funnel`
- `GET /api/v1/tracker/sources`
- `GET /api/v1/settings/ai`
- `GET /api/v1/settings/ai/status`
- `POST /api/v1/settings/ai`
- `POST /api/v1/settings/ai/test`
- `DELETE /api/v1/settings/ai`

## Configurações de IA

Os endpoints `settings/ai` retornam apenas dados seguros:

- `provider`;
- `model`;
- `configured`;
- `status`;
- toggles de uso por módulo;
- warnings;
- `updated_at`.

A chave nunca é retornada ao frontend. O armazenamento local separa metadados e segredo:

```txt
data/settings/ai-settings.json
data/secrets/ai-provider.local.json
```

`data/` e os arquivos locais de segredo são ignorados pelo Git. O provider `local` não faz chamada
externa, `gemini` usa a integração backend existente e `openai_future` permanece planejado.

## Segurança

- nao expor API keys no frontend;
- nao retornar API keys nos endpoints `settings/ai`;
- nao salvar API keys em `localStorage` ou `sessionStorage`;
- nao usar `*` no CORS por default;
- nao salvar curriculo bruto em records do tracker;
- nao calcular Match Score real no frontend;
- nao inferir credenciais, empregos, formacoes ou certificacoes sem evidencia;
- usar `fallback_payload` do GitHub Analyzer apenas com dados publicos/capturados conscientemente.
- nao alterar scraper autenticado, Chromium/CDP, crawler logado ou auto-apply neste layer.

## Contratos relacionados

- [API contract](../08-frontend/api-contract.md)
- [Mock data contract](../08-frontend/mock-data-contract.md)
- [Lovable handoff](../08-frontend/lovable-handoff.md)
- [Application Intelligence](../08-frontend/application-intelligence.md)
