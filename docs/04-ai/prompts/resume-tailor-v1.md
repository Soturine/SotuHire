# Prompt: Resume Tailor v1

## Metadata

```txt
PROMPT_ID: resume_tailor_v1
PROMPT_VERSION: 1.0.0
STATUS: reviewed for v1.0.0; safe fallback and Match Engine 2.0 evidence integration available
OWNER: SotuHire
USED_BY: modules/recommendations, modules/ats
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Gerar sugestões de adaptação segura do currículo para uma vaga específica, com base em evidências.

## When to use

- Depois da extração de currículo, extração de vaga, ATS e matching.
- Quando usuário quer adaptar texto para uma vaga.
- Quando há gaps e keywords seguras.

## When not to use

- Não usar para criar experiência falsa.
- Não usar sem perfil/vaga estruturados.
- Não usar para substituir revisão humana.

## Input contract

```json
{
  "resume_text": "string",
  "candidate_profile": "object",
  "job_post": "object",
  "match_analysis": "MatchResultV2 | object",
  "ats_analysis": "object",
  "evidence_sources": {
    "resume": "object | null",
    "github": "object | null",
    "portfolio": "object | null",
    "memory": "object | null"
  },
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "tailored_summary": {
    "text": "string",
    "supported_by": ["string"],
    "safety_notes": ["string"]
  },
  "section_suggestions": [
    {
      "section": "summary | skills | experience | education | projects | certifications | other",
      "action": "rewrite | reorder | highlight | add_if_true | remove | clarify",
      "suggestion": "string",
      "supported_by": ["string"],
      "condition": "string | null",
      "risk_of_overclaiming": "low | medium | high"
    }
  ],
  "safe_resume_bullets": [
    {
      "bullet": "string",
      "supported_by": ["string"],
      "confidence": 0.0
    }
  ],
  "do_not_claim": ["string"],
  "review_required": true
}
```

## System prompt

```txt
Você adapta currículo com segurança. Não invente fatos. Toda sugestão forte deve ter suporte em evidência. Para informações não explícitas, use linguagem condicional.
```

## User prompt template

```txt
Gere sugestões seguras para adaptar o currículo à vaga.

=== CURRÍCULO ===
{resume_text}

=== PERFIL ===
{candidate_profile}

=== VAGA ===
{job_post}

=== MATCH ===
{match_analysis}

=== ATS ===
{ats_analysis}
```

## Calibration rules

- Bullets fortes precisam de evidência.
- Se a pessoa talvez tenha uma skill mas não está claro, usar `add_if_true`.
- Listar explicitamente o que não deve ser reivindicado.
- Registro profissional, formação e certificação só podem ser destacados como fato quando a
  evidência existir.
- Para gap crítico, orientar revisão de compatibilidade da vaga em vez de maquiagem curricular.
- Projeto pessoal ou GitHub pode virar evidência de projeto, não experiência corporativa.

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
- Do not suggest adding COREN, CRP, CREA, CAU or similar as fact without evidence.
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

- tailor dev
- tailor enfermagem
- tailor arquitetura
- tailor curso técnico

## Related modules

- modules/recommendations
- modules/ats
- modules/matching
