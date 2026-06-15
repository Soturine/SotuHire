# Prompt: Job Extraction Multi-Domain v1

## Metadata

```txt
PROMPT_ID: job_extraction_multi_domain_v1
PROMPT_VERSION: 1.0.0
STATUS: planned for v0.10.0
OWNER: SotuHire
USED_BY: modules/jobs, modules/domain_intelligence, modules/ai
DEFAULT_TEMPERATURE: 0.1
REQUIRES_STRUCTURED_OUTPUT: true
REQUIRES_HUMAN_REVIEW_ON_LOW_CONFIDENCE: true
```

## Purpose

Extrair dados estruturados de uma vaga de qualquer área profissional, classificando requisitos, domínio e criticidade.

## When to use

- Quando o usuário cola uma descrição de vaga.
- Quando uma vaga é capturada por extensão/URL/fonte pública.
- Quando o sistema precisa separar obrigatório, desejável, responsabilidade e benefício.

## When not to use

- Não usar para avaliar currículo.
- Não usar para gerar candidatura.
- Não usar para calcular score final.

## Input contract

```json
{
  "job_text": "string",
  "source": {
    "type": "manual | url | extension | public_source | pasted_post",
    "url": "string | null",
    "platform": "string | null"
  },
  "candidate_context": {
    "target_domains": ["string"],
    "locations": ["string"],
    "work_models": ["string"]
  },
  "language": "pt-BR"
}
```

## Output schema

```json
{
  "job_identity": {
    "title": "string | null",
    "company": "string | null",
    "source": "string | null",
    "url": "string | null",
    "location": "string | null",
    "work_model": "remote | hybrid | onsite | field | unknown",
    "contract_type": "clt | pj | internship | temporary | freelance | public_sector | unknown",
    "salary": "string | null",
    "confidence": 0.0
  },
  "domain_classification": {
    "primary_domain": "string",
    "secondary_domains": ["string"],
    "is_tech_job": true,
    "is_regulated_profession": true,
    "confidence": 0.0,
    "evidence": ["string"]
  },
  "seniority": {
    "level": "intern | assistant | junior | mid | senior | specialist | coordinator | manager | director | unknown",
    "evidence": ["string"],
    "confidence": 0.0
  },
  "requirements": [
    {
      "text": "string",
      "normalized_name": "string",
      "category": "education | hard_skill | soft_skill | tool | software | equipment | certification | professional_license | language | experience | methodology | regulation | responsibility | availability | location | portfolio | other",
      "importance": "required | preferred | optional | unclear",
      "criticality": "low | medium | high | knockout",
      "evidence": "string",
      "confidence": 0.0
    }
  ],
  "responsibilities": ["string"],
  "benefits": ["string"],
  "keywords_for_ats": ["string"],
  "red_flags": [
    {
      "type": "vague_salary | excessive_requirements | unpaid_work | suspicious_contact | unrealistic_seniority | discrimination | other",
      "description": "string",
      "severity": "low | medium | high"
    }
  ],
  "missing_job_information": ["string"],
  "extraction_confidence": {
    "overall": 0.0,
    "needs_user_review": true
  }
}
```

## System prompt

```txt
Você é um especialista em análise de vagas, requisitos profissionais e ATS. A vaga pode ser de qualquer área: TI, cybersecurity, engenharia biomédica, enfermagem, pedagogia, psicologia, engenharia civil, arquitetura, design de interiores, administração, humanas, exatas, cursos técnicos, saúde, educação, indústria, financeiro, marketing ou outras. Retorne somente JSON válido. Não invente empresa, salário, requisitos ou benefícios. Diferencie requisito obrigatório de desejável.
```

## User prompt template

```txt
Analise a vaga abaixo e retorne somente JSON no schema definido.

=== FONTE ===
{source}

=== CONTEXTO DO CANDIDATO ===
{candidate_context}

=== TEXTO DA VAGA ===
{job_text}
```

## Calibration rules

- Se a vaga usa termos como “obrigatório”, “necessário”, “imprescindível”, classificar como required.
- Se usa “desejável”, “diferencial”, “será um plus”, classificar como preferred.
- Se exige registro profissional, criticality deve ser high ou knockout.
- Se a vaga for post informal, reduzir confidence geral.
- Se salário não for informado, usar null.

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

- job_dev_backend.txt
- job_enfermeiro_uti.txt
- job_professor_fundamental.txt
- job_psicologo_rh.txt
- job_engenheiro_civil_obras.txt
- job_arquiteto_interiores.txt
- job_tecnico_manutencao.txt

## Related modules

- modules/jobs
- modules/domain_intelligence
- modules/ai/schemas/job_extraction.py
