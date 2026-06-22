# API contract v1

Este documento define contratos futuros para um frontend moderno. A v1.1.0 não implementa
todos estes endpoints. Ela documenta a fronteira para Lovable, React, Vite, Next.js ou
outro frontend consumir depois.

## Convenções

- Base futura local: `http://127.0.0.1:<port>/api/v1`
- Formato: JSON.
- IDs: strings estáveis geradas pelo backend.
- Erros: payloads com `error.code`, `error.message` e `error.details`.
- Segurança: CORS restrito em API real; nunca expor API keys no frontend.

## GET /api/v1/health

- Objetivo: verificar se a API local está ativa.
- Request JSON: nenhum.
- Response JSON:

```json
{
  "status": "ok",
  "version": "1.1.0",
  "local_first": true,
  "capabilities": ["resume_extract", "job_extract", "match", "tracker"]
}
```

- Erros possíveis: `service_unavailable`.
- Segurança: não retornar segredos ou paths sensíveis.
- Equivalente atual: Local Companion API já possui health check.
- Status: parcialmente existente.

## POST /api/v1/resume/extract

- Objetivo: extrair perfil estruturado de currículo.
- Request JSON:

```json
{
  "resume_text": "Texto fictício do currículo",
  "language": "pt-BR",
  "options": {"use_ai": false}
}
```

- Response JSON:

```json
{
  "profile": {
    "name": "Pessoa Fictícia",
    "headline": "Desenvolvedora Backend",
    "skills": ["Python", "FastAPI"],
    "experience": [],
    "education": [],
    "projects": []
  },
  "confidence": 0.82,
  "warnings": []
}
```

- Erros possíveis: `invalid_payload`, `resume_too_short`, `unsupported_file_type`.
- Segurança: currículo é dado sensível; manter local por padrão.
- Equivalente atual: parsers e extração estruturada em `modules/parsers` e `modules/ai`.
- Status: futuro endpoint.

## POST /api/v1/job/extract

- Objetivo: transformar vaga em requisitos estruturados.
- Request JSON:

```json
{
  "job_text": "Descrição fictícia da vaga",
  "source_url": "https://example.invalid/jobs/backend",
  "language": "pt-BR"
}
```

- Response JSON:

```json
{
  "job": {
    "title": "Backend Developer",
    "company": "Empresa Fictícia",
    "required_skills": ["Python", "APIs"],
    "preferred_skills": ["Docker"],
    "domain": "technology"
  },
  "confidence": 0.86
}
```

- Erros possíveis: `job_too_short`, `invalid_url`, `unsupported_language`.
- Segurança: não acessar fontes autenticadas sem ação explícita.
- Equivalente atual: `modules/parsers/job_description_parser.py` e extrator estruturado.
- Status: futuro endpoint.

## POST /api/v1/match/analyze

- Objetivo: calcular match entre currículo, vaga e evidências.
- Request JSON:

```json
{
  "profile": {"skills": ["Python", "FastAPI"]},
  "job": {"required_skills": ["Python", "Docker"]},
  "evidence": {"github": [], "portfolio": []}
}
```

- Response JSON:

```json
{
  "analysis_version": "match_engine_v2",
  "match_score": 78,
  "confidence_score": 0.66,
  "evidence_score": 72,
  "critical_gaps": [],
  "safe_actions": ["Evidencie Docker somente se tiver experiência real."]
}
```

- Erros possíveis: `missing_resume`, `missing_job`, `low_confidence`.
- Segurança: score real deve vir do backend/core.
- Equivalente atual: `modules/matching` e `modules/analyzer`.
- Status: futuro endpoint.

## POST /api/v1/ats/analyze

- Objetivo: revisar alinhamento ATS sem incentivar invenção.
- Request JSON:

```json
{
  "resume_text": "string",
  "job_keywords": ["Python", "Docker"],
  "match_analysis": {"analysis_version": "match_engine_v2"}
}
```

- Response JSON:

```json
{
  "ats_score": 74,
  "present": ["Python"],
  "missing_but_safe_to_add_if_true": ["Docker"],
  "missing_without_evidence": ["Kubernetes"]
}
```

- Erros possíveis: `missing_match_analysis`, `invalid_keywords`.
- Segurança: separar keyword segura de keyword sem evidência.
- Equivalente atual: `modules/ats`.
- Status: futuro endpoint.

## POST /api/v1/resume/tailor

- Objetivo: gerar sugestões seguras de ajuste de currículo.
- Request JSON:

```json
{
  "profile": {"skills": ["Python"]},
  "job": {"required_skills": ["Python", "Docker"]},
  "ats_review": {"present": ["Python"]},
  "match_analysis": {"critical_gaps": []}
}
```

- Response JSON:

```json
{
  "safe_keywords": ["Python"],
  "suggested_bullets": [
    "Descreva projetos Python com contexto, impacto e evidências verificáveis."
  ],
  "warnings": ["Não declare Docker sem experiência real."]
}
```

- Erros possíveis: `insufficient_evidence`, `invalid_profile`.
- Segurança: nunca gerar credencial, cargo ou experiência falsa.
- Equivalente atual: `modules/resume_tailor`.
- Status: futuro endpoint.

## POST /api/v1/github/repo/analyze

- Objetivo: analisar repositório público como evidência técnica.
- Request JSON:

```json
{
  "repo_url": "https://github.com/example/fictitious-api",
  "include_files": true
}
```

- Response JSON:

```json
{
  "repo": "example/fictitious-api",
  "quality_score": 81,
  "languages": ["Python"],
  "evidence": ["README com instalação", "testes automatizados"],
  "risks": []
}
```

- Erros possíveis: `repo_not_found`, `private_repo`, `rate_limited`.
- Segurança: análise pública básica não deve exigir token no frontend.
- Equivalente atual: `modules/github_analyzer`.
- Status: futuro endpoint.

## GET /api/v1/tracker/jobs

- Objetivo: listar vagas salvas.
- Request JSON: nenhum.
- Response JSON:

```json
{
  "jobs": [
    {
      "id": "job_demo_001",
      "title": "Backend Developer",
      "company": "Empresa Fictícia",
      "status": "applied",
      "match_score": 78
    }
  ]
}
```

- Erros possíveis: `storage_unavailable`.
- Segurança: retornar apenas dados locais autorizados.
- Equivalente atual: tracker local.
- Status: futuro endpoint.

## POST /api/v1/tracker/jobs

- Objetivo: salvar nova vaga no tracker.
- Request JSON:

```json
{
  "title": "Backend Developer",
  "company": "Empresa Fictícia",
  "source": "LinkedIn",
  "status": "saved"
}
```

- Response JSON:

```json
{"id": "job_demo_001", "status": "saved"}
```

- Erros possíveis: `invalid_status`, `duplicate_job`.
- Segurança: deduplicação e validação ficam no backend.
- Equivalente atual: tracker local.
- Status: futuro endpoint.

## PATCH /api/v1/tracker/jobs/{id}

- Objetivo: atualizar status, notas ou metadados de uma vaga.
- Request JSON:

```json
{
  "status": "interview",
  "notes": "Entrevista técnica marcada."
}
```

- Response JSON:

```json
{"id": "job_demo_001", "status": "interview", "updated": true}
```

- Erros possíveis: `job_not_found`, `invalid_status`, `conflict`.
- Segurança: preservar histórico de mudanças quando disponível.
- Equivalente atual: tracker local.
- Status: futuro endpoint.

## GET /api/v1/tracker/metrics

- Objetivo: retornar KPIs agregados.
- Request JSON: nenhum.
- Response JSON:

```json
{
  "total_saved": 18,
  "total_applied": 9,
  "average_match": 73,
  "response_rate": 0.33,
  "interview_rate": 0.22,
  "offer_rate": 0.05
}
```

- Erros possíveis: `not_enough_data`, `storage_unavailable`.
- Segurança: agregações oficiais vêm do backend.
- Equivalente atual: dashboard/tracker.
- Status: futuro endpoint.

## GET /api/v1/tracker/requirements

- Objetivo: ranquear requisitos, skills ausentes e gaps críticos.
- Request JSON: nenhum.
- Response JSON: ver `docs/assets/mock-api/tracker-requirements.json`.
- Erros possíveis: `not_enough_data`.
- Segurança: não inferir skills como possuídas sem evidência.
- Equivalente atual: `rank_applied_requirements`.
- Status: futuro endpoint.

## GET /api/v1/tracker/funnel

- Objetivo: retornar funil de candidaturas.
- Request JSON: nenhum.
- Response JSON:

```json
{
  "stages": [
    {"status": "saved", "count": 18},
    {"status": "applied", "count": 9},
    {"status": "interview", "count": 2},
    {"status": "offer", "count": 1}
  ]
}
```

- Erros possíveis: `storage_unavailable`.
- Segurança: usar dados locais agregados.
- Equivalente atual: métricas do tracker.
- Status: futuro endpoint.

## GET /api/v1/tracker/sources

- Objetivo: comparar fontes de vagas e resultados.
- Request JSON: nenhum.
- Response JSON:

```json
{
  "sources": [
    {"name": "LinkedIn", "saved": 8, "applied": 4, "average_match": 76},
    {"name": "Gupy", "saved": 5, "applied": 3, "average_match": 69}
  ]
}
```

- Erros possíveis: `not_enough_data`.
- Segurança: não armazenar credenciais de portais no frontend.
- Equivalente atual: tracker e normalização de fontes.
- Status: futuro endpoint.

