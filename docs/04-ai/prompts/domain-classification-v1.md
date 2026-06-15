# Prompt: Domain Classification v1

## Metadata

```txt
PROMPT_ID: domain_classification_v1
PROMPT_VERSION: 1.0.0
STATUS: planned for v0.10.0
OWNER: SotuHire
USED_BY: modules/domain_intelligence
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Classificar domínio profissional de currículo, vaga ou projeto, detectando áreas primárias, secundárias e categorias de requisitos.

## When to use

- Quando uma vaga/currículo/projeto precisa ser encaixado em domínios.
- Quando o sistema precisa carregar catálogo específico.
- Quando há mistura de áreas.

## When not to use

- Não usar para gerar sugestões de currículo.
- Não usar sozinho para decidir match final.

## Input contract

```json
{
  "text": "string",
  "text_type": "resume | job | project | profile | post",
  "known_context": "object | null",
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "primary_domain": {
    "name": "string",
    "confidence": 0.0,
    "evidence": ["string"]
  },
  "secondary_domains": [
    {
      "name": "string",
      "confidence": 0.0,
      "evidence": ["string"]
    }
  ],
  "requirement_categories_detected": ["string"],
  "regulated_profession_signals": [
    {
      "credential": "string",
      "evidence": "string",
      "confidence": 0.0
    }
  ],
  "domain_notes": ["string"],
  "needs_review": true
}
```

## System prompt

```txt
Você classifica domínios profissionais. Use evidência textual. Não force tudo para tecnologia. Aceite domínios mistos. Retorne somente JSON válido.
```

## User prompt template

```txt
Classifique o domínio profissional do texto abaixo.

Tipo: {text_type}
Contexto conhecido: {known_context}

Texto:
{text}
```

## Calibration rules

- Se houver múltiplos domínios relevantes, listar secundários.
- Se o texto for genérico, usar confidence baixo.
- Se houver credencial como COREN/CRP/CREA/CAU, marcar sinal de profissão regulamentada.

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

- texto vaga enfermagem
- texto vaga dev
- texto currículo engenharia biomédica
- texto projeto GitHub educacional

## Related modules

- modules/domain_intelligence/classifier.py
- modules/domain_intelligence/catalog_loader.py
