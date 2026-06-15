# Prompt Architecture

Este documento define como os prompts do SotuHire devem ser organizados, versionados, testados e usados.

## Objetivo

Evitar prompts soltos, pequenos demais ou difíceis de validar.

Cada função de IA deve ter:

- prompt específico;
- versão;
- contrato de entrada;
- schema de saída;
- regras anti-invenção;
- regras de confiança;
- critérios de falha;
- exemplos;
- testes.

## Filosofia

A IA interpreta, extrai, classifica, resume e sugere.

O código valida, calcula score, aplica pesos, salva histórico e bloqueia resultados inseguros.

```txt
IA = interpretação e estruturação
Código = validação, cálculo e persistência
```

## Fluxo padrão

```txt
Input bruto
  ↓
Pré-processamento local
  ↓
Prompt versionado
  ↓
Resposta JSON
  ↓
JSON Guard
  ↓
Schema Pydantic
  ↓
Confidence Merger
  ↓
Score calculado pelo código
  ↓
UI de revisão quando necessário
```

## Princípios

### 1. Um prompt por tarefa

Não usar um prompt genérico para currículo, vaga, matching, ATS e GitHub.

Cada tarefa tem objetivo, entrada e saída diferentes.

### 2. JSON rígido

Prompts devem retornar JSON válido, sem Markdown e sem texto extra.

### 3. Pydantic como contrato

A saída da IA só é aceita se passar por schema.

### 4. Confidence por campo

Cada campo relevante deve informar confiança.

### 5. Anti-invenção

A IA não pode inventar fatos profissionais.

### 6. Human review

Campos críticos com baixa confiança devem ser revisados pelo usuário.

## Tipos de prompt

| Prompt | Função |
|---|---|
| Resume Extraction | Extrair currículo bruto para perfil estruturado. |
| Job Extraction | Extrair vaga para requisitos estruturados. |
| Domain Classification | Detectar área profissional e categorias de requisitos. |
| Match Analysis | Comparar vaga e perfil por evidências. |
| ATS Analysis | Avaliar estrutura e aderência ATS. |
| Resume Tailor | Sugerir adaptação segura do currículo. |
| GitHub Repo Analysis | Avaliar repositório como evidência técnica e profissional. |
| GitHub Profile Analysis | Avaliar perfil GitHub agregado. |
| Portfolio Gap Analysis | Identificar lacunas no portfólio. |
| Hidden Job Detection | Detectar oportunidade em texto informal. |
| Career Advice | Gerar plano de evolução profissional. |

## Estrutura obrigatória de cada prompt doc

Cada arquivo em `docs/04-ai/prompts/` deve conter:

- metadata;
- propósito;
- quando usar;
- quando não usar;
- input contract;
- output schema;
- system prompt;
- user prompt template;
- regras de calibração;
- regras de confiança;
- regras anti-invenção;
- exemplos;
- failure modes;
- estratégia de retry;
- módulos relacionados.

## Modelo de metadata

```yaml
prompt_id: resume_extraction_v1
version: 1.0.0
status: planned
owner: SotuHire
used_by:
  - modules.ai.orchestration
  - modules.resume
requires:
  - JSON guard
  - Pydantic schema
  - confidence merger
```

## Configuração recomendada

```txt
temperature: 0.1
top_p: baixo/médio
response_format: JSON
retry_on_invalid_json: true
max_retries: 2
```

## Falhas comuns

- JSON inválido.
- Campo obrigatório ausente.
- Invenção de credencial.
- Confundir curso com certificação.
- Confundir projeto pessoal com experiência profissional.
- Transformar competência transferível em match completo.
- Criar score final sem explicação.

## Estratégia de retry

1. Validar JSON.
2. Se inválido, reenviar apenas erro de schema e pedir correção.
3. Se continuar inválido, cair para fallback heurístico.
4. Marcar resultado como `needs_user_review`.

## Relação com código

Os prompts documentados aqui devem virar implementações em:

```txt
modules/ai/prompts/
modules/ai/schemas/
modules/ai/prompt_registry.py
modules/ai/json_guard.py
modules/ai/orchestration.py
```
