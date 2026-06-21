# Prompt: GitHub Repo Analysis v2

## Metadata

```txt
PROMPT_ID: github_repo_analysis_v2
PROMPT_VERSION: 2.0.0
STATUS: implemented in v0.11.0
OWNER: SotuHire
USED_BY: modules/github_analyzer, modules/portfolio
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Avaliar um repositório GitHub como evidência técnica e profissional para currículo, portfólio e candidaturas.

## When to use

- Quando usuário cola URL de repo.
- Quando extensão detecta owner/repo.
- Quando sistema precisa avaliar projeto como evidência de carreira.
- Quando há vaga-alvo para comparar repo x vaga.

## When not to use

- Não usar apenas com texto visível do DOM se backend puder usar GitHub API.
- Não usar para auditar repositórios privados sem autorização.
- Não usar para inventar métricas ou tecnologias.

## Input contract

```json
{
  "repository": {
    "owner": "string",
    "name": "string",
    "url": "string",
    "description": "string | null",
    "default_branch": "string | null",
    "created_at": "string | null",
    "updated_at": "string | null",
    "stars": "number | null",
    "forks": "number | null",
    "topics": ["string"],
    "languages": {"language": "percentage_or_bytes"},
    "license": "string | null"
  },
  "analysis_context": {
    "mode": "technical_quality | portfolio_value | job_alignment | resume_evidence | full",
    "target_role": "string | null",
    "target_job": "object | null",
    "candidate_profile": "object | null",
    "career_domains": ["string"],
    "language": "pt-BR"
  },
  "repository_structure": "string",
  "selected_files": [
    {
      "path": "string",
      "reason_selected": "priority_file | dependency_central | config | readme | workflow | source | test | sample",
      "content": "string"
    }
  ],
  "detected_signals": {
    "has_readme": true,
    "has_tests": true,
    "has_ci": true,
    "has_docker": true,
    "has_docs": true,
    "has_license": true,
    "has_env_example": true,
    "has_package_manifest": true,
    "has_security_policy": true
  }
}
```

## Output schema

```json
{
  "repository_identity": {
    "owner": "string",
    "name": "string",
    "url": "string",
    "project_type": "web_app | api | library | cli | data_science | mobile | extension | automation | academic | unknown",
    "detected_domains": ["string"],
    "confidence": 0.0
  },
  "executive_summary": {
    "short_summary": "string",
    "professional_summary": "string",
    "recruiter_summary": "string",
    "limitations": ["string"]
  },
  "dimension_scores": {
    "tests": 0,
    "security": 0,
    "architecture": 0,
    "code_quality": 0,
    "documentation": 0,
    "consistency": 0,
    "maintainability": 0,
    "portfolio_value": 0,
    "resume_evidence": 0,
    "recruiter_readiness": 0,
    "job_alignment": 0
  },
  "tech_stack": {
    "languages": ["string"],
    "frameworks": ["string"],
    "libraries": ["string"],
    "tools": ["string"],
    "databases": ["string"],
    "devops": ["string"],
    "testing_tools": ["string"],
    "detected_from_files": [
      {
        "technology": "string",
        "evidence_file": "string",
        "confidence": 0.0
      }
    ]
  },
  "architecture": {
    "rating": "excellent | good | fair | poor | unclear",
    "style": "layered | mvc | modular | monolith | microservices | event_driven | unknown",
    "entry_points": ["string"],
    "important_modules": [
      {
        "path": "string",
        "role": "string",
        "evidence": "string"
      }
    ],
    "positive_signals": ["string"],
    "problems": ["string"],
    "improvement_suggestions": ["string"]
  },
  "portfolio_value": {
    "best_fit_roles": ["string"],
    "skills_demonstrated": [
      {
        "skill": "string",
        "category": "language | framework | architecture | testing | devops | security | data | ux | documentation | domain | soft_skill",
        "evidence_files": ["string"],
        "confidence": 0.0
      }
    ],
    "career_strengths": ["string"],
    "career_weaknesses": ["string"],
    "how_to_present_in_interview": ["string"]
  },
  "resume_evidence": {
    "safe_resume_bullets": [
      {
        "bullet": "string",
        "supported_by": ["string"],
        "confidence": 0.0,
        "risk_of_overclaiming": "low | medium | high"
      }
    ],
    "skills_to_add_if_true": ["string"],
    "do_not_claim": ["string"]
  },
  "security": {
    "risk_level": "low | medium | high | critical | unclear",
    "security_flags": [
      {
        "severity": "low | medium | high | critical",
        "type": "secret | injection | auth | dependency | data_exposure | insecure_config | other",
        "description": "string",
        "evidence_file": "string | null",
        "recommendation": "string"
      }
    ],
    "positive_security_signals": ["string"]
  },
  "evidence_index": [
    {
      "claim": "string",
      "source_file": "string",
      "evidence_type": "file_presence | code_content | config | readme | workflow | dependency | tree",
      "confidence": 0.0
    }
  ],
  "final_verdict": {
    "is_portfolio_ready": true,
    "main_blockers": ["string"],
    "next_3_actions": ["string"],
    "one_sentence_verdict": "string"
  }
}
```

## System prompt

```txt
Você é um avaliador sênior de qualidade de software, arquitetura, segurança, documentação e valor de portfólio profissional. Analise apenas as evidências fornecidas: metadados, README, árvore, arquivos selecionados, workflows, dependências, commits se fornecidos, vaga-alvo se fornecida. Retorne somente JSON válido. Não invente tecnologias, métricas, usuários, empresas, deploys ou resultados. Se testes aparecem na árvore, reconheça presença de testes mesmo sem conteúdo.
```

## User prompt template

```txt
Analise o repositório abaixo.

=== REPOSITORY METADATA ===
{repository}

=== ANALYSIS CONTEXT ===
{analysis_context}

=== DETECTED SIGNALS ===
{detected_signals}

=== COMPLETE DIRECTORY TREE ===
{repository_structure}

=== SELECTED FILES ===
{selected_files}

Retorne apenas o JSON no schema definido.
```

## Calibration rules

- Se houver segredo real exposto, security <= 2.
- Se projeto não trivial não tiver testes, tests <= 3.
- Se README promete feature não encontrada, adicionar inconsistência.
- Não penalizar ausência de deploy se o projeto não promete deploy.
- Não gerar bullet de currículo sem evidência.

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

- repo_python_fastapi
- repo_streamlit_app
- repo_browser_extension
- repo_no_tests
- repo_no_readme
- repo_with_ci

## Related modules

- modules/github_analyzer
- modules/portfolio
- browser-extension/github_injected.js
