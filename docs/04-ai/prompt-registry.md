# Prompt Registry

## Objetivo

O Prompt Registry é o ponto central para registrar, carregar, versionar e executar prompts no SotuHire.

Ele evita que prompts fiquem espalhados em serviços diferentes e facilita testes, auditoria e evolução.

## Problema

Sem registry, o projeto tende a ter:

- prompts duplicados;
- schemas inconsistentes;
- modelos chamados de formas diferentes;
- dificuldade de versionar;
- dificuldade de testar;
- dificuldade de auditar uma análise antiga.

## Solução

Criar uma camada de registro:

```txt
modules/ai/prompt_registry.py
```

E uma estrutura de prompts e schemas:

```txt
modules/ai/prompts/
modules/ai/schemas/
```

## Interface sugerida

```python
@dataclass(frozen=True)
class PromptSpec:
    prompt_id: str
    version: str
    system_prompt: str
    user_template: str
    output_schema: type[BaseModel]
    temperature: float = 0.1
    requires_review: bool = True
    max_retries: int = 2
```

## Métodos esperados

```python
class PromptRegistry:
    def register(self, spec: PromptSpec) -> None: ...
    def get(self, prompt_id: str, version: str | None = None) -> PromptSpec: ...
    def list_prompts(self) -> list[PromptSpec]: ...
    def render_user_prompt(self, prompt_id: str, payload: dict) -> str: ...
```

## Execução sugerida

```python
result = ai_orchestrator.run_structured(
    prompt_id="resume_extraction_v1",
    payload={"resume_text": text},
    provider="gemini",
)
```

## Responsabilidades

O Prompt Registry deve:

- mapear prompt_id para PromptSpec;
- garantir versão;
- expor schema esperado;
- renderizar template;
- manter metadados;
- facilitar testes.

O Prompt Registry não deve:

- chamar API diretamente;
- calcular score de negócio;
- salvar dados de candidatura;
- tomar decisões finais.

## Relação com providers

Providers como Gemini, OpenAI-compatible ou local models devem ficar atrás de uma interface.

```txt
AIProvider
  generate_text(...)
  generate_json(...)
  supports_structured_output
```

O registry não deve depender de um provider específico.

## Relação com JSON Guard

Depois de chamar a IA, a resposta deve passar por:

```txt
raw_response
-> json_guard.parse
-> pydantic_schema.validate
-> confidence rules
-> result object
```

## Relação com scoring

Prompts podem retornar sinais, evidências e sugestões de score.

O score final deve ser calculado pelo código.

Exemplo:

```json
{
  "suggested_score_inputs": {
    "required_requirements_coverage": 0.82,
    "evidence_strength": 0.74,
    "risk_penalty": 0.10
  }
}
```

O código transforma isso em score final com regras versionadas.

## Auditoria

Cada execução deve permitir responder:

- qual prompt foi usado?
- qual versão?
- qual modelo?
- qual schema?
- o JSON validou?
- quais campos vieram com baixa confiança?
- houve fallback?

## Roadmap de implementação

### v0.10.0

- Prompt Registry básico.
- Resume extraction.
- Job extraction.
- Domain classification.
- JSON Guard.
- Pydantic schemas.

### v0.11.0

- GitHub Analyzer prompts.
- Portfolio prompts.
- Evidence index.

### v0.12.0

- Matching prompts.
- ATS prompts.
- Tailor prompts.
- Career advice prompts.
