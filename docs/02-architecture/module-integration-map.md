# Mapa de integração de módulos

Este mapa registra como a v1.5.0 conecta `modules/`, FastAPI e `apps/web` sem mover regra de
negócio para o frontend.

## Fluxo principal

```text
apps/web (React/Vite)
  -> apps/api/routes
  -> apps/api/services
  -> modules/*
  -> data local ignorado pelo Git quando há persistência
```

O frontend mostra estado, modo Demo/API Real, badges de provider e warnings. O backend/core calcula
scores, valida evidências, aplica regras anti-invenção e decide fallback.

## Integrações

| Domínio | Core | API | Frontend | Observação |
| --- | --- | --- | --- | --- |
| Currículo | `modules/parsers`, `modules/ai/structured_resume_extractor.py` | `POST /api/v1/resume/extract` | `/resume` | Gemini opcional via `resume_extraction_v1`; fallback local. |
| Vaga | `modules/parsers`, `modules/ai/structured_job_extractor.py` | `POST /api/v1/job/extract` | `/job` | Gemini opcional via `job_extraction_multi_domain_v1`; fallback local. |
| Compatibilidade | `modules/analyzer`, `modules/matching`, `modules/ai/structured_analysis.py` | `POST /api/v1/match/analyze` | `/match` | Prompt `match_analysis_evidence_based_v1`; Match Engine local preserva score final. |
| ATS | `modules/ats` | `POST /api/v1/ats/analyze` | `/ats` | Score local; IA opcional só adiciona insights seguros. |
| Tailor | `modules/resume_tailor` | `POST /api/v1/resume/tailor` | `/tailor` | Saída segura local; IA opcional aparece separada. |
| GitHub | `modules/github_analyzer` | `POST /api/v1/github/repo/analyze` | `/github` | Provider opcional entra no analyzer; scores finais seguem por código. |
| Tracker | `modules/tracker`, `modules/storage` | `/api/v1/tracker/*` | `/tracker`, `/intelligence` | Persistência local e métricas. |
| IA e Providers | `modules/ai/providers`, `apps/api/services/ai_settings.py` | `/api/v1/settings/ai*` | `/settings` | Chave nunca retorna ao frontend. |
| Fontes autenticadas autorizadas | `modules/scraping/*` | `/api/v1/sources/authenticated-browser/*` | `/sources` | Fluxo existente; sem auto-apply e sem login automatizado. |
| Extensão Local | `browser-extension/`, `modules/local_api` | `/api/v1/extension/*` | `/sources` | Ponte para capturas locais já salvas. |
| Streamlit | `app.py`, `modules/ui` | Não | Legado/dev | Mantido para debug local e fluxos antigos. |
| Concursos/Editais | `modules/public_exams` | Não | Não | Roadmap isolado. |

## Roteamento de IA

`apps/api/services/ai_settings.py` seleciona o runtime por área:

- `use_ai=false`, provider `local` ou toggle desligado: usa provider local determinístico.
- `provider=gemini`, chave salva no backend e toggle ligado: usa Gemini via Prompt Registry.
- falha de provider: fallback local com warning.
- `openai_future`: status planejado, sem chamada externa.

Toggles:

```txt
allow_match
allow_ats
allow_tailor
allow_github
allow_memory_context
```

Currículo e vaga usam IA quando `use_ai=true` e `provider=gemini` configurado, pois são etapas de
extração. A UI mostra o provider e campos de baixa confiança sem expor segredo.

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
