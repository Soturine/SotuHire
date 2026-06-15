# Prompt Registry

O Prompt Registry é a camada planejada para registrar, versionar e executar prompts do SotuHire.

## Objetivo

Centralizar todos os prompts de IA para evitar chamadas soltas espalhadas pelo código.

## Problema atual

Sem registry, cada módulo tende a montar seu próprio prompt. Isso dificulta:

- versionamento;
- testes;
- auditoria;
- troca de provider;
- validação de schema;
- comparação entre versões;
- reprodutibilidade de análises.

## Modelo planejado

```python
@dataclass(frozen=True)
class PromptSpec:
    prompt_id: str
    version: str
    system_prompt: str
    user_template: str
    output_schema: type[BaseModel]
    temperature: float = 0.1
    max_retries: int = 2
```

## Interface planejada

```python
class PromptRegistry:
    def get(self, prompt_id: str, version: str | None = None) -> PromptSpec:
        ...

    def render_user_prompt(self, prompt_id: str, payload: dict) -> str:
        ...

    def validate_output(self, prompt_id: str, raw_json: str) -> BaseModel:
        ...
```

## Prompts registrados inicialmente

- `resume_extraction_v1`;
- `job_extraction_multi_domain_v1`;
- `domain_classification_v1`;
- `match_analysis_evidence_based_v1`;
- `ats_analysis_v1`;
- `resume_tailor_v1`;
- `github_repo_analysis_v2`;
- `github_profile_analysis_v1`;
- `portfolio_gap_analysis_v1`;
- `hidden_job_detection_v1`;
- `career_advice_v1`.

## Dados salvos por execução

Cada execução de prompt deve registrar:

```json
{
  "prompt_id": "resume_extraction_v1",
  "prompt_version": "1.0.0",
  "provider": "gemini",
  "model": "configured-model",
  "input_hash": "sha256",
  "schema_version": "1.0.0",
  "created_at": "timestamp",
  "status": "success | fallback | failed",
  "confidence": 0.0
}
```

## Regras

- Nunca chamar provider direto de módulo de negócio.
- Sempre validar saída.
- Sempre versionar prompt.
- Sempre salvar prompt_id e prompt_version quando houver resultado persistido.
- Sempre marcar fallback quando IA falhar.
- Nunca confiar em score calculado apenas pela IA quando houver engine determinística.

## Relação com providers

O registry não deve depender de Gemini diretamente.

Ele deve funcionar com qualquer provider compatível com texto e JSON estruturado.

## Critérios de pronto

- Todos os prompts carregados por ID.
- Schemas Pydantic vinculados.
- Retry em JSON inválido.
- Fallback documentado.
- Testes unitários para pelo menos três prompts.
- Fixtures cobrindo múltiplas áreas.
