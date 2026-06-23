# Mapa de integração de módulos

Este mapa registra como a v1.5.1 conecta `apps/web`, FastAPI e `modules/` sem mover regra de
negócio para o frontend.

```text
apps/web (React/Vite)
  -> apps/api/routes
  -> apps/api/services
  -> modules/*
  -> data local ignorado pelo Git quando há persistência
```

O frontend mostra estado, modo Demo/API Real, badges de provider e warnings. O backend/core calcula
scores, valida evidências, aplica regras anti-invenção e decide fallback.

## Matriz principal

| Funcionalidade | Tela frontend | Endpoint API | Service backend | Módulo core | Status real |
| --- | --- | --- | --- | --- | --- |
| Currículo | `/resume` | `POST /api/v1/resume/extract` | `extract_resume` | `modules/parsers`, structured extractor | Real |
| Vaga | `/job` | `POST /api/v1/job/extract` | `extract_job` | `modules/parsers`, structured extractor | Real |
| Compatibilidade | `/match` | `POST /api/v1/match/analyze` | `analyze_match` | `modules/analyzer`, `modules/matching` | Real |
| ATS | `/ats` | `POST /api/v1/ats/analyze` | `analyze_ats` | `modules/ats` | Real |
| Tailor | `/tailor` | `POST /api/v1/resume/tailor` | `tailor_resume` | `modules/resume_tailor` | Real |
| GitHub | `/github` | `POST /api/v1/github/repo/analyze` | `analyze_github_repo` | `modules/github_analyzer`, `modules/portfolio` | Real |
| Tracker | `/tracker` | `GET/POST/PATCH /api/v1/tracker/jobs` | `apps.api.services.tracker` | `modules/tracker`, `modules/storage` | Real |
| Intelligence | `/intelligence` | `/api/v1/tracker/metrics`, `/requirements`, `/funnel`, `/sources` | tracker service | `modules/tracker` | Real |
| IA e Providers | `/settings` | `/api/v1/settings/ai*` | `apps.api.services.ai_settings` | `modules/ai/providers` | Real |
| Extensão Local | `/sources` | `/api/v1/extension/*` | `apps.api.services.extension` | `modules/local_api`, `browser-extension/` | Real |
| Navegador autenticado autorizado | `/sources` | `/api/v1/sources/authenticated-browser/*` | `apps.api.services.sources` | fluxo existente de scraping local | Parcial |
| Streamlit | legado/dev | Não é API web | `app.py`, `modules/ui` | core antigo | Legado |
| Concursos/Editais | sem tela web | sem endpoint web | Parcial | `modules/public_exams` | Roadmap |

## Roteamento de IA

`apps/api/services/ai_settings.py` seleciona o runtime por área:

- `use_ai=false`, provider `local` ou toggle desligado: provider local determinístico.
- `provider=gemini`, chave salva no backend e toggle ligado: Gemini via Prompt Registry.
- falha de provider: fallback local com warning.
- `openai_future`: status planejado, sem chamada externa.

Toggles atuais:

```txt
allow_match
allow_ats
allow_tailor
allow_github
allow_memory_context
```

Currículo e vaga usam IA quando `use_ai=true` e `provider=gemini` configurado. A UI mostra provider,
modo e baixa confiança sem expor segredo.

## Ponte da extensão

Endpoints FastAPI:

```txt
GET  /api/v1/extension/status
GET  /api/v1/extension/captures
GET  /api/v1/extension/profile-analysis
POST /api/v1/extension/import/job
POST /api/v1/extension/import/github
POST /api/v1/extension/import/tracker
```

A ponte lê o store local da Local Companion API e permite importar capturas para Vaga, GitHub ou
Candidaturas. Ela não reimplementa crawler logado, não controla contas de terceiros e não altera o
browser autenticado existente.

## UX web v1.5.1

- Home e Dashboard exibem fluxo guiado de 8 passos.
- Currículo, Vaga, Match, ATS, Tailor e GitHub exibem estado Local/IA/Fallback.
- Match, ATS, Tailor e GitHub separam pontos fortes, lacunas, sugestões práticas, riscos, próximas
  ações e itens que não devem ser adicionados sem evidência.
- Fontes e Captura mostra status do companion, últimas capturas, origem, data, tipo e ações.
- Kanban mostra origem, score, última análise, notas e data.
