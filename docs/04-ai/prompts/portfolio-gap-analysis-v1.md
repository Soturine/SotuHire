# Prompt: Portfolio Gap Analysis v1

## Metadata

```txt
PROMPT_ID: portfolio_gap_analysis_v1
PROMPT_VERSION: 1.0.0
STATUS: planned for v0.11.0
OWNER: SotuHire
USED_BY: modules/portfolio, modules/recommendations
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Identificar lacunas de portfólio em relação ao objetivo profissional ou vaga alvo.

## When to use

- Depois de analisar GitHub, portfólio e currículo.
- Quando usuário quer melhorar portfólio.
- Quando há alvo de vaga ou domínio.

## When not to use

- Não usar para avaliar uma vaga.
- Não usar para recomendar projetos impossíveis ou grandes demais.

## Input contract

```json
{
  "candidate_profile": "object",
  "portfolio_reports": ["object"],
  "github_reports": ["object"],
  "target_roles": ["string"],
  "target_job": "object | null",
  "constraints": {
    "time_available": "string | null",
    "skill_level": "string | null"
  },
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "portfolio_strengths": ["string"],
  "portfolio_gaps": [
    {
      "gap": "string",
      "why_it_matters": "string",
      "priority": "high | medium | low",
      "suggested_action": "string",
      "estimated_effort": "small | medium | large"
    }
  ],
  "recommended_project_improvements": ["string"],
  "recommended_new_projects": [
    {
      "idea": "string",
      "skills_demonstrated": ["string"],
      "scope_warning": "string"
    }
  ],
  "next_3_actions": ["string"]
}
```

## System prompt

```txt
Você analisa lacunas de portfólio com foco prático e proporcional. Não recomende overengineering. Não invente projetos existentes. Retorne JSON.
```

## User prompt template

```txt
Analise lacunas do portfólio.

Perfil: {candidate_profile}
Portfólio: {portfolio_reports}
GitHub: {github_reports}
Cargos alvo: {target_roles}
Vaga alvo: {target_job}
Restrições: {constraints}
```

## Calibration rules

- Priorizar melhorias pequenas e de alto impacto.
- Para júnior/estágio, não exigir arquitetura enterprise.
- Recomendação deve ser executável.

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

- portfolio_dev_backend
- portfolio_cybersecurity
- portfolio_architecture_design
- portfolio_education

## Related modules

- modules/portfolio
- modules/recommendations
