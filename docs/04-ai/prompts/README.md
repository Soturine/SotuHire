# Prompts

Esta pasta contém os prompts planejados, implementados ou revisados para o SotuHire.

Cada prompt é documentado como um contrato funcional, não apenas como texto para copiar e colar.

## Estrutura padrão

Cada documento deve conter:

- metadata;
- purpose;
- when to use;
- when not to use;
- input contract;
- output schema;
- system prompt;
- user prompt template;
- calibration rules;
- confidence rules;
- anti-fabrication rules;
- domain-specific rules;
- failure modes;
- retry strategy;
- test fixtures;
- related modules.

## Prompts disponíveis

- `resume-extraction-v1.md`
- `job-extraction-multi-domain-v1.md`
- `domain-classification-v1.md`
- `match-analysis-evidence-based-v1.md`
- `ats-analysis-v1.md`
- `resume-tailor-v1.md`
- `github-repo-analysis-v2.md`
- `github-profile-analysis-v1.md`
- `portfolio-gap-analysis-v1.md`
- `hidden-job-detection-v1.md`
- `career-advice-v1.md`

## Regra de ouro

Prompts podem gerar estrutura e interpretação.

O código deve validar e decidir.
