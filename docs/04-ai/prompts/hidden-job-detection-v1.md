# Prompt: Hidden Job Detection v1

## Metadata

```txt
PROMPT_ID: hidden_job_detection_v1
PROMPT_VERSION: 1.0.0
STATUS: planned for v0.10+
OWNER: SotuHire
USED_BY: modules/jobs, modules/search_intelligence
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Detectar oportunidades de vaga em textos públicos, posts informais e páginas com sinais de contratação.

## When to use

- Quando o usuário cola um post público.
- Quando fonte pública traz texto com possível vaga.
- Quando sistema precisa extrair oportunidade informal.

## When not to use

- Não usar para acessar conteúdo privado.
- Não usar para inferir contato pessoal não fornecido.
- Não usar para automatizar candidatura.

## Input contract

```json
{
  "source_text": "string",
  "source_metadata": {
    "url": "string | null",
    "platform": "string | null",
    "captured_at": "string | null"
  },
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "is_job_opportunity": true,
  "confidence": 0.0,
  "extracted_job": {
    "title": "string | null",
    "company": "string | null",
    "location": "string | null",
    "work_model": "remote | hybrid | onsite | field | unknown",
    "requirements": ["string"],
    "contact_or_apply_instruction": "string | null",
    "deadline": "string | null"
  },
  "evidence": ["string"],
  "missing_information": ["string"],
  "risk_flags": ["string"],
  "needs_user_review": true
}
```

## System prompt

```txt
Você detecta oportunidades de vaga em textos públicos. Retorne JSON. Seja conservador. Se não for claramente vaga, confidence baixo. Não invente empresa, contato ou requisito.
```

## User prompt template

```txt
Analise o texto público abaixo para detectar possível oportunidade.

Metadata: {source_metadata}

Texto:
{source_text}
```

## Calibration rules

- Post informal com “estamos contratando” deve ser oportunidade.
- Texto institucional genérico sem vaga deve ser false ou confidence baixo.
- Se contato não aparece, usar null.

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

- post_linkedin_publico
- pagina_carreira
- post_evento_sem_vaga
- texto_informal_com_email

## Related modules

- modules/jobs
- modules/search_intelligence
