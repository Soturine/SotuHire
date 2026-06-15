# Prompt: ATS Analysis v1

## Metadata

```txt
PROMPT_ID: ats_analysis_v1
PROMPT_VERSION: 1.0.0
STATUS: planned for v0.12.0
OWNER: SotuHire
USED_BY: modules/ats, modules/recommendations
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Avaliar currículo para ATS considerando uma vaga específica, sem sugerir invenção de informações.

## When to use

- Quando há currículo e vaga estruturados.
- Quando o usuário quer melhorar aderência ATS.
- Antes de gerar Resume Tailor.

## When not to use

- Não usar para extrair currículo bruto.
- Não usar para escrever currículo inteiro do zero com dados inventados.

## Input contract

```json
{
  "resume_text": "string",
  "candidate_profile": "object",
  "job_post": "object",
  "match_signals": "object | null",
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "ats_score_inputs": {
    "structure": 0.0,
    "keyword_alignment": 0.0,
    "clarity": 0.0,
    "specificity": 0.0,
    "format_risk": 0.0,
    "job_alignment": 0.0
  },
  "strong_points": ["string"],
  "weak_points": ["string"],
  "missing_sections": ["string"],
  "keyword_suggestions": [
    {
      "keyword": "string",
      "source": "job_requirement",
      "safe_to_add": true,
      "condition": "string"
    }
  ],
  "rewrite_suggestions": [
    {
      "section": "summary | experience | skills | education | projects | other",
      "current_issue": "string",
      "suggested_change": "string",
      "safety_note": "string"
    }
  ],
  "ats_risks": [
    {
      "risk": "string",
      "severity": "low | medium | high",
      "fix": "string"
    }
  ],
  "final_recommendations": ["string"]
}
```

## System prompt

```txt
Você é um especialista em ATS, clareza de currículo e adaptação segura para vagas. Retorne somente JSON. Não invente experiência. Use “se for verdadeiro” quando sugerir destacar algo não explícito.
```

## User prompt template

```txt
Avalie o currículo para ATS em relação à vaga.

=== CURRÍCULO ===
{resume_text}

=== PERFIL ESTRUTURADO ===
{candidate_profile}

=== VAGA ===
{job_post}

=== MATCH SIGNALS ===
{match_signals}
```

## Calibration rules

- Keywords não evidenciadas devem ir para `missing_and_not_evidenced` ou sugestão condicional.
- Problemas de formatação devem ser separados de problemas de conteúdo.
- Não sugerir adicionar certificação/registro sem evidência.

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

- ATS dev
- ATS enfermagem
- ATS engenharia civil
- ATS pedagogia

## Related modules

- modules/ats
- modules/recommendations
- modules/matching
