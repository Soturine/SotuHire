# API contract v1.2.0

Este contrato descreve a FastAPI local implementada na v1.2.0 para consumo por Lovable,
React, Vite, Next.js ou outro frontend moderno.

Base local padrao:

```text
http://127.0.0.1:8787/api/v1
```

OpenAPI:

```text
http://127.0.0.1:8787/openapi.json
http://127.0.0.1:8787/docs
```

## Convencoes

- Formato: JSON.
- Envelope de sucesso:

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "request_id": ""
}
```

- Envelope de erro:

```json
{
  "ok": false,
  "error": {
    "code": "invalid_payload",
    "message": "Payload invalido para o contrato da API.",
    "details": {}
  },
  "request_id": ""
}
```

- CORS e restrito por default. Configure origens com `SOTUHIRE_API_ALLOWED_ORIGINS`.
- A API e local-first. Nao coloque Gemini key, GitHub token ou secrets no frontend.
- Curriculo bruto entra somente no request necessario; respostas de extracao removem `raw_text`
  por default.
- Regras de Match, ATS, Resume Tailor, GitHub Analyzer e Application Intelligence ficam no backend.

## GET /api/v1/health

Verifica se a API local esta ativa.

Response `data`:

```json
{
  "status": "ok",
  "service": "sotuhire-api",
  "version": "1.2.0",
  "local_first": true,
  "openapi_url": "/openapi.json",
  "docs_url": "/docs",
  "capabilities": [
    "resume_extract",
    "job_extract",
    "match_analyze",
    "ats_analyze",
    "resume_tailor",
    "github_repo_analyze",
    "tracker_jobs",
    "application_intelligence"
  ]
}
```

## POST /api/v1/resume/extract

Extrai `ResumeProfileSchema` a partir de texto colado.

Request:

```json
{
  "resume_text": "Texto ficticio do curriculo",
  "source_type": "text",
  "include_raw_text": false,
  "request_id": "ui_001"
}
```

Response `data`:

```json
{
  "profile": {
    "name": "Pessoa Ficticia",
    "email": "pessoa@example.invalid",
    "skills": ["Python", "FastAPI"],
    "experiences": [],
    "projects": [],
    "raw_text": ""
  },
  "confidence": 0.85
}
```

## POST /api/v1/job/extract

Extrai `JobPostingSchema` a partir de descricao de vaga.

Request:

```json
{
  "job_text": "Cargo: Backend Python\nRequisitos: Python, FastAPI, SQL",
  "source_url": "https://example.invalid/jobs/backend",
  "include_raw_text": false
}
```

Response `data`:

```json
{
  "job": {
    "title": "Backend Python",
    "company": "",
    "modality": "unknown",
    "required_skills": ["Python", "SQL", "FastAPI"],
    "desired_skills": [],
    "ats_keywords": ["backend", "python"],
    "raw_text": ""
  },
  "confidence": 0.75
}
```

Warnings podem incluir dados ausentes como salario, empresa ou modalidade.

## POST /api/v1/match/analyze

Calcula match usando o fluxo local estruturado e Match Engine 2.0.

Request minimo:

```json
{
  "resume_text": "Texto ficticio do curriculo",
  "job_text": "Descricao ficticia da vaga",
  "preferences": null,
  "github_evidence": [],
  "portfolio_evidence": []
}
```

Tambem aceita `profile` e `job` ja estruturados quando o frontend executou as extracoes antes.

Response `data`:

```json
{
  "provider_used": "local",
  "local_first": true,
  "analysis": {
    "match_score": 78,
    "ats_score": 74,
    "opportunity_fit_score": 70,
    "risk_score": 20,
    "recommendation": "apply_with_adjustments",
    "analysis_version": "match_engine_v2",
    "confidence_score": 0.66,
    "evidence_score": 72,
    "matched_requirements": [],
    "partial_requirements": [],
    "missing_requirements": [],
    "critical_gaps": [],
    "safe_actions": []
  }
}
```

## POST /api/v1/ats/analyze

Classifica keywords ATS usando evidencia do Match Engine 2.0.

Request:

```json
{
  "resume_text": "Texto ficticio do curriculo",
  "job_text": "Descricao ficticia da vaga",
  "job_keywords": ["Python", "Docker"],
  "match_analysis": null
}
```

Response `data`:

```json
{
  "ats_score": 74,
  "present": ["Python"],
  "missing_but_safe_to_add_if_true": ["Docker"],
  "missing_without_evidence": []
}
```

## POST /api/v1/resume/tailor

Gera sugestoes seguras de ajuste do curriculo sem inventar experiencia.

Request:

```json
{
  "target_role": "Backend Python",
  "target_company": "Empresa Ficticia",
  "job_text": "Descricao ficticia da vaga",
  "evidence_text": "Evidencias fornecidas pela pessoa usuaria",
  "match_analysis": null
}
```

Response `data`:

```json
{
  "safe_to_export": true,
  "tailor": {
    "target_role": "Backend Python",
    "target_company": "Empresa Ficticia",
    "section_order": ["Resumo", "Projetos", "Skills"],
    "improved_bullets": [],
    "keywords_added": ["Python"],
    "evidence_used": [],
    "warnings": []
  }
}
```

## POST /api/v1/github/repo/analyze

Analisa repositorio publico como evidencia tecnica.

Request:

```json
{
  "repo_url": "https://github.com/example/fictitious-api",
  "mode": "full",
  "target_role": "Backend Python",
  "target_job": {},
  "candidate_profile": {},
  "career_domains": ["software"],
  "language": "pt-BR",
  "fallback_payload": null
}
```

Response `data`:

```json
{
  "report": {
    "repository_identity": {
      "owner": "example",
      "name": "fictitious-api",
      "url": "https://github.com/example/fictitious-api",
      "project_type": "api"
    },
    "scores": {
      "overall_score": 81,
      "grade": "B"
    },
    "provider_used": "local",
    "fallback_used": false
  }
}
```

`fallback_payload` aceita sinais publicos capturados pela extensao quando a GitHub API falha.

## GET /api/v1/tracker/jobs

Lista registros locais do tracker.

Response `data`:

```json
{
  "jobs": [
    {
      "id": "job_demo_001",
      "job_title": "Backend Python",
      "company": "Empresa Ficticia",
      "status": "applied",
      "requirements": ["Python", "Docker"],
      "analysis": {
        "match_score": 82,
        "ats_score": 74
      }
    }
  ]
}
```

## POST /api/v1/tracker/jobs

Cria ou atualiza um card do tracker local.

Request:

```json
{
  "title": "Backend Python",
  "company": "Empresa Ficticia",
  "source_url": "https://linkedin.com/jobs/123",
  "requirements": ["Python", "Docker"],
  "status": "applied",
  "match_score": 82,
  "ats_score": 74,
  "privacy_acknowledged": true
}
```

Response `data`:

```json
{
  "job": {
    "id": "generated_id",
    "job_title": "Backend Python",
    "status": "applied"
  }
}
```

## PATCH /api/v1/tracker/jobs/{id}

Atualiza status e/ou notas.

Request:

```json
{
  "status": "interview",
  "notes": "Entrevista tecnica marcada."
}
```

## GET /api/v1/tracker/metrics

Retorna KPIs do tracker.

Response `data`:

```json
{
  "total_saved": 18,
  "total_applied": 9,
  "by_status": {
    "applied": 9,
    "interview": 2,
    "offer": 1
  },
  "average_match_by_status": {
    "applied": 75
  },
  "response_rate": 0.33,
  "interview_rate": 0.22,
  "offer_rate": 0.05
}
```

## GET /api/v1/tracker/requirements

Retorna rankings de requisitos e gaps para Application Intelligence.

Response `data`:

```json
{
  "top_requirements": [
    {
      "name": "Python",
      "count": 12,
      "status_scope": "all",
      "sources": ["linkedin.com"],
      "candidate_has_evidence": true
    }
  ],
  "missing_requirements": [],
  "critical_gaps": [],
  "requirements_by_source": [
    {"source": "linkedin.com", "requirement": "Python", "count": 6}
  ]
}
```

## GET /api/v1/tracker/funnel

Retorna funil salvo -> aplicado -> resposta -> entrevista -> oferta.

Response `data`:

```json
{
  "stages": [
    {"status": "saved", "label": "Salvas", "count": 18},
    {"status": "applied", "label": "Aplicadas", "count": 9},
    {"status": "response", "label": "Com resposta", "count": 3},
    {"status": "interview", "label": "Entrevistas", "count": 2},
    {"status": "offer", "label": "Oferta", "count": 1}
  ],
  "conversion_rates": [
    {"from": "saved", "to": "applied", "rate": 0.5}
  ]
}
```

## GET /api/v1/tracker/sources

Compara fontes/domains de vagas.

Response `data`:

```json
{
  "sources": [
    {
      "name": "linkedin.com",
      "saved": 8,
      "applied": 4,
      "interviews": 1,
      "average_match": 76,
      "top_requirements": ["Python", "Docker"]
    }
  ]
}
```

## Variaveis de ambiente

| Variavel | Default | Uso |
| --- | --- | --- |
| `SOTUHIRE_API_HOST` | `127.0.0.1` | Host usado por `scripts/run_api.py`. |
| `SOTUHIRE_API_PORT` | `8787` | Porta local usada por `scripts/run_api.py`. |
| `SOTUHIRE_API_ALLOWED_ORIGINS` | origens locais + GitHub Pages | Lista CSV para CORS. |
| `GITHUB_TOKEN` | vazio | Token opcional usado pelo GitHub Analyzer core. |
