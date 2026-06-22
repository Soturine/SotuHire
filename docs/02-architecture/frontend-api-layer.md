# Frontend API Layer

A v1.2.0 adiciona uma camada FastAPI local em `apps/api`. Ela existe para conectar um frontend
moderno ao core Python sem mover regra critica para JavaScript.

## Objetivo

- expor contratos HTTP versionados em `/api/v1`;
- manter Streamlit como app local atual/dev;
- manter Local Companion API como ponte da extensao assistiva;
- preparar Lovable, React, Vite ou Next.js para consumir endpoints reais;
- preservar privacidade local-first e anti-fabrication.

## Entrada

```bash
python scripts/run_api.py
```

Ou diretamente:

```bash
uvicorn apps.api.main:app --host 127.0.0.1 --port 8787
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

## Endpoints v1.2.0

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

## Segurança

- nao expor API keys no frontend;
- nao usar `*` no CORS por default;
- nao salvar curriculo bruto em records do tracker;
- nao calcular Match Score real no frontend;
- nao inferir credenciais, empregos, formacoes ou certificacoes sem evidencia;
- usar `fallback_payload` do GitHub Analyzer apenas com dados publicos/capturados conscientemente.

## Contratos relacionados

- [API contract](../08-frontend/api-contract.md)
- [Mock data contract](../08-frontend/mock-data-contract.md)
- [Lovable handoff](../08-frontend/lovable-handoff.md)
- [Application Intelligence](../08-frontend/application-intelligence.md)
