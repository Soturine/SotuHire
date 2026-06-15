# Prompt: Resume Extraction v1

## Metadata

```txt
PROMPT_ID: resume_extraction_v1
PROMPT_VERSION: 1.0.0
STATUS: planned for v0.10.0
OWNER: SotuHire
USED_BY: modules/ai, modules/parsers, modules/profile
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Extrair um currículo bruto em um perfil profissional estruturado, multiárea e com confidence por campo.

## When to use

- Quando o usuário envia PDF, DOCX, TXT ou texto colado de currículo.
- Quando o sistema precisa atualizar o CandidateProfile.
- Quando a heurística local extraiu texto, mas precisa de estrutura semântica.

## When not to use

- Não usar para adaptar currículo para uma vaga específica.
- Não usar para calcular match final.
- Não usar para inventar dados ausentes.

## Input contract

```json
{
  "resume_text": "string",
  "file_type": "pdf | docx | txt | pasted_text",
  "candidate_preferences": {
    "target_roles": ["string"],
    "target_domains": ["string"],
    "locations": ["string"],
    "work_models": ["remote | hybrid | onsite | field"],
    "seniority_target": "string | null"
  },
  "existing_profile_memory": "object | null",
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "candidate_identity": {
    "name": "string | null",
    "email_present": true,
    "phone_present": true,
    "location": "string | null",
    "links": ["string"],
    "confidence": 0.0
  },
  "professional_summary": {
    "current_headline": "string | null",
    "inferred_headline": "string | null",
    "summary_text": "string | null",
    "confidence": 0.0
  },
  "domains": [
    {
      "domain": "software | cybersecurity | engineering | biomedical_engineering | civil_engineering | nursing | psychology | pedagogy | architecture | interior_design | business | finance | marketing | technical | humanities | healthcare | education | other",
      "confidence": 0.0,
      "evidence": ["string"]
    }
  ],
  "seniority": {
    "estimated_level": "intern | junior | mid | senior | specialist | coordinator | manager | unknown",
    "reasoning": "string",
    "confidence": 0.0
  },
  "education": [
    {
      "course": "string",
      "institution": "string | null",
      "degree_type": "technical | bachelor | licentiate | postgraduate | mba | course | certification | unknown",
      "status": "completed | ongoing | interrupted | unknown",
      "start_date": "string | null",
      "end_date": "string | null",
      "confidence": 0.0
    }
  ],
  "experiences": [
    {
      "title": "string",
      "company": "string | null",
      "start_date": "string | null",
      "end_date": "string | null",
      "responsibilities": ["string"],
      "achievements": ["string"],
      "tools_or_methods": ["string"],
      "domain": "string | null",
      "confidence": 0.0
    }
  ],
  "skills": [
    {
      "name": "string",
      "normalized_name": "string",
      "category": "hard_skill | soft_skill | tool | software | equipment | methodology | language | certification | professional_license | regulation | domain_knowledge",
      "evidence": ["string"],
      "confidence": 0.0
    }
  ],
  "licenses_and_credentials": [
    {
      "name": "string",
      "type": "professional_license | certification | course | regulatory_training",
      "status": "active | expired | unknown | not_informed",
      "evidence": "string",
      "confidence": 0.0
    }
  ],
  "languages": [
    {
      "language": "string",
      "level": "basic | intermediate | advanced | fluent | native | unknown",
      "confidence": 0.0
    }
  ],
  "projects": [
    {
      "name": "string",
      "description": "string",
      "technologies_or_methods": ["string"],
      "evidence": "string",
      "confidence": 0.0
    }
  ],
  "ats_observations": {
    "missing_sections": ["string"],
    "weak_sections": ["string"],
    "strong_sections": ["string"],
    "format_risks": ["string"],
    "keyword_risks": ["string"]
  },
  "extraction_confidence": {
    "overall": 0.0,
    "low_confidence_fields": ["string"],
    "needs_user_review": true
  }
}
```

## System prompt

```txt
Você é um especialista em análise de currículos, ATS e estruturação de perfil profissional. Extraia apenas informações evidenciadas no currículo. Retorne somente JSON válido. Não use markdown. Não invente experiência, formação, certificação, registro profissional, idioma ou resultado. Se uma informação não estiver clara, use null ou confidence baixo. Detecte áreas profissionais mesmo quando não forem TI. Para áreas regulamentadas, trate registros profissionais com cuidado.
```

## User prompt template

```txt
Analise o currículo abaixo e retorne o JSON no schema definido.

=== CONTEXTO ===
File type: {file_type}
Preferências: {candidate_preferences}
Memória existente: {existing_profile_memory}
Idioma: {language}

=== CURRÍCULO ===
{resume_text}
```

## Calibration rules

- Se o currículo não informa registro profissional, não criar registro.
- Se o currículo informa curso, não converter em certificação.
- Se senioridade não estiver clara, usar `unknown` ou confidence baixo.
- Se o texto vier de PDF quebrado, reduzir confidence geral.
- Se houver conflito entre memória e currículo, priorizar o currículo atual e marcar revisão.

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

- resume_dev_backend.txt
- resume_enfermagem.txt
- resume_pedagogia.txt
- resume_psicologia.txt
- resume_engenharia_civil.txt
- resume_tecnico_eletrotecnica.txt

## Related modules

- modules/parsers
- modules/profile
- modules/ai/schemas/resume_extraction.py
- modules/ai/prompt_registry.py
