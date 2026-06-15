# Prompt: Career Advice v1

## Metadata

```txt
PROMPT_ID: career_advice_v1
PROMPT_VERSION: 1.0.0
STATUS: planned for v0.12.0
OWNER: SotuHire
USED_BY: modules/recommendations, modules/profile, modules/tracker
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Gerar recomendações de evolução profissional com base em evidências do perfil, candidaturas, vagas e portfólio.

## When to use

- Quando usuário quer plano de melhoria.
- Depois de analisar currículo, vagas e portfólio.
- Quando tracker mostra padrões de rejeição/lacunas.

## When not to use

- Não usar como orientação legal/médica/financeira.
- Não prometer emprego.
- Não reforçar insegurança ou comparação com outras pessoas.

## Input contract

```json
{
  "candidate_profile": "object",
  "job_targets": ["object"],
  "match_history": ["object"],
  "portfolio_reports": ["object"],
  "tracker_summary": "object | null",
  "constraints": "object | null",
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "career_summary": "string",
  "priority_gaps": [
    {
      "gap": "string",
      "evidence": ["string"],
      "impact": "high | medium | low",
      "suggested_action": "string"
    }
  ],
  "next_30_days_plan": ["string"],
  "next_90_days_plan": ["string"],
  "resume_actions": ["string"],
  "portfolio_actions": ["string"],
  "job_search_actions": ["string"],
  "warnings": ["string"],
  "confidence": 0.0
}
```

## System prompt

```txt
Você gera recomendações de carreira práticas, honestas e baseadas em evidências. Não prometa emprego. Não invente experiência. Não reforce comparações negativas. Retorne JSON.
```

## User prompt template

```txt
Gere plano de evolução profissional com base nos dados.

Perfil: {candidate_profile}
Vagas alvo: {job_targets}
Histórico de matches: {match_history}
Portfólio: {portfolio_reports}
Tracker: {tracker_summary}
Restrições: {constraints}
```

## Calibration rules

- Plano deve ser proporcional ao nível do candidato.
- Priorizar ações concretas.
- Separar currículo, portfólio e busca de vagas.
- Se dados forem insuficientes, marcar confidence baixo.

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

- career_dev_junior
- career_enfermagem
- career_transicao
- career_engenharia

## Related modules

- modules/recommendations
- modules/profile
- modules/tracker
