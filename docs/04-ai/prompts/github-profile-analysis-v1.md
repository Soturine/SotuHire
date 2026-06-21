# Prompt: GitHub Profile Analysis v1

## Metadata

```txt
PROMPT_ID: github_profile_analysis_v1
PROMPT_VERSION: 1.0.0
STATUS: reviewed in v0.11.0; deep profile pipeline future
OWNER: SotuHire
USED_BY: modules/github_analyzer, modules/portfolio
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Avaliar um perfil GitHub como sinal de portfólio profissional, considerando repositórios, consistência, stack e prontidão para recrutador.

## When to use

- Quando usuário informa perfil GitHub.
- Quando sistema precisa resumir portfólio geral.
- Quando há objetivo de carreira ou vaga alvo.

## When not to use

- Não usar para avaliar profundamente um repo específico.
- Não usar para inferir experiência corporativa sem evidência.

## Input contract

```json
{
  "profile": {
    "username": "string",
    "url": "string",
    "bio": "string | null",
    "pinned_repositories": ["object"],
    "repositories_summary": ["object"],
    "languages_summary": "object",
    "topics_summary": ["string"]
  },
  "candidate_profile": "object | null",
  "target_job": "object | null",
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "profile_summary": "string",
  "portfolio_positioning": "string",
  "strong_signals": ["string"],
  "weak_signals": ["string"],
  "best_repositories_to_highlight": [
    {
      "repo": "string",
      "why": "string",
      "best_fit_roles": ["string"],
      "confidence": 0.0
    }
  ],
  "skills_evidenced_across_profile": [
    {
      "skill": "string",
      "evidence": ["string"],
      "confidence": 0.0
    }
  ],
  "recommendations": ["string"],
  "needs_review": true
}
```

## System prompt

```txt
Você avalia perfis GitHub como portfólio profissional. Não invente experiência. Diferencie projeto pessoal, acadêmico, biblioteca, fork e experimento. Retorne somente JSON.
```

## User prompt template

```txt
Avalie o perfil GitHub abaixo.

Perfil: {profile}
Candidato: {candidate_profile}
Vaga alvo: {target_job}
```

## Calibration rules

- Não tratar estrela/fork como qualidade absoluta.
- Priorizar evidências de projeto, README, testes, consistência e stack.
- Se o perfil tem poucos dados, reduzir confidence.

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

- profile_dev_junior
- profile_many_forks
- profile_academic_projects
- profile_security_labs

## Related modules

- modules/github_analyzer
- modules/portfolio
