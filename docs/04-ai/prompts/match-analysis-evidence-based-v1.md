# Prompt: Match Analysis Evidence-Based v1

## Metadata

```txt
PROMPT_ID: match_analysis_evidence_based_v1
PROMPT_VERSION: 1.0.0
STATUS: planned for v0.12.0
OWNER: SotuHire
USED_BY: modules/matching
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Comparar perfil estruturado, vaga estruturada e evidências adicionais para gerar sinais de matching explicáveis.

## When to use

- Quando já existem CandidateProfile e JobPost estruturados.
- Quando o sistema possui evidências de currículo, GitHub, portfólio ou memória.
- Antes do score final calculado pelo código.

## When not to use

- Não usar com texto bruto sem extração prévia.
- Não usar para decidir score final sozinho.
- Não usar para inventar competências.

## Input contract

```json
{
  "candidate_profile": "object",
  "job_post": "object",
  "evidence_sources": {
    "resume": "object | null",
    "github": "object | null",
    "portfolio": "object | null",
    "memory": "object | null"
  },
  "candidate_preferences": "object | null",
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "match_overview": {
    "summary": "string",
    "candidate_fit_level": "low | medium | good | strong | unclear",
    "confidence": 0.0
  },
  "requirement_matches": [
    {
      "job_requirement": "string",
      "importance": "required | preferred | optional | unclear",
      "match_status": "matched | partial | missing | unclear",
      "candidate_evidence": ["string"],
      "evidence_source": "resume | github | portfolio | memory | none",
      "gap_severity": "none | low | medium | high | knockout",
      "recommendation": "string"
    }
  ],
  "critical_gaps": [
    {
      "gap": "string",
      "why_it_matters": "string",
      "can_be_fixed_in_resume": true,
      "safe_action": "string"
    }
  ],
  "transferable_skills": [
    {
      "candidate_skill": "string",
      "could_help_with": "string",
      "explanation": "string",
      "confidence": 0.0
    }
  ],
  "ats_keywords": {
    "present": ["string"],
    "missing_but_true_candidate_may_add": ["string"],
    "missing_and_not_evidenced": ["string"]
  },
  "suggested_score_inputs": {
    "required_requirements_coverage": 0.0,
    "preferred_requirements_coverage": 0.0,
    "seniority_fit": 0.0,
    "domain_fit": 0.0,
    "ats_keyword_fit": 0.0,
    "evidence_strength": 0.0,
    "risk_penalty": 0.0
  },
  "final_notes": {
    "best_argument_for_application": "string",
    "biggest_risk": "string",
    "next_actions": ["string"]
  }
}
```

## System prompt

```txt
Você é um analista de compatibilidade entre currículo, vaga e evidências profissionais. Compare apenas com base nas evidências fornecidas. Não invente competências. Não calcule score final absoluto; retorne sinais para o código calcular.
```

## User prompt template

```txt
Compare o perfil e a vaga abaixo.

=== PERFIL ===
{candidate_profile}

=== VAGA ===
{job_post}

=== EVIDÊNCIAS ===
{evidence_sources}

=== PREFERÊNCIAS ===
{candidate_preferences}
```

## Calibration rules

- Requisito obrigatório ausente deve gerar gap mais grave.
- Registro profissional ausente quando exigido deve ser knockout ou high.
- Competências transferíveis devem ter explicação e confidence.
- Não marcar como matched sem evidência.

## Confidence rules

- Use `confidence` from `0.0` to `1.0`.
- Use lower confidence when the source text is vague, incomplete, informal, noisy or contradictory.
- Use higher confidence only when the evidence is explicit.
- Fields with confidence below `0.70` should be marked for human review.
- Do not use confidence as a quality score for the candidate. Confidence is about extraction certainty.

## Anti-fabrication rules

- Do not invent experience.
- Do not invent education.
- Do not invent company names.
- Do not invent certifications.
- Do not invent professional licenses.
- Do not invent languages.
- Do not invent technologies.
- Do not invent metrics.
- Do not convert personal projects into professional employment.
- Do not convert a course into a certification unless the source says it is a certification.

## Failure modes

- Invalid JSON.
- Missing required field.
- Unsupported enum value.
- Hallucinated evidence.
- Overconfident inference.
- Mixed language output.
- Markdown returned instead of JSON.

## Retry strategy

1. Try local JSON parsing.
2. If parsing fails, call JSON repair.
3. If schema validation fails, retry with validation errors.
4. If retry fails, use fallback heuristics.
5. Mark output as `needs_review`.

## Test fixtures

- match dev backend
- match enfermagem UTI
- match pedagogia inclusão
- match engenharia civil obras
- match psicologia RH

## Related modules

- modules/matching/engine_v2.py
- modules/matching/requirement_matcher.py
- modules/matching/evidence_matcher.py
