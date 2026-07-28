# Taxonomia de erros de provider

`ProviderError` normaliza falhas Gemini/OpenAI nos campos `provider`, `model`, `status_code`, `error_code`, `error_type`, `category`, `retryable`, `retry_after_seconds`, `request_id`, `sanitized_message`, `attempt`, `max_attempts` e `occurred_at`.

Categorias: `AUTHENTICATION`, `PERMISSION`, `INSUFFICIENT_QUOTA`, `RATE_LIMIT`, `BILLING_REQUIRED`, `PROJECT_LIMIT`, `MODEL_NOT_FOUND`, `MODEL_UNAVAILABLE`, `INVALID_REQUEST`, `SAFETY_BLOCK`, `SCHEMA_INVALID`, `EMPTY_RESPONSE`, `TRUNCATED_RESPONSE`, `TIMEOUT`, `NETWORK`, `PROVIDER_INTERNAL` e `UNKNOWN`.

## Regras de decisão

| Sinal | Categoria | Retry imediato |
|---|---|---|
| OpenAI `insufficient_quota` | `INSUFFICIENT_QUOTA` | não |
| billing inativo/requerido | `BILLING_REQUIRED` | não |
| limite de projeto/organização | `PROJECT_LIMIT` | não |
| 429 temporário/`Retry-After` | `RATE_LIMIT` | sim, limitado |
| Gemini `RESOURCE_EXHAUSTED` de requisições | `RATE_LIMIT` | sim, limitado |
| 503/modelo em alta demanda | `MODEL_UNAVAILABLE` | sim, limitado |

Quota, billing e project limit são `BLOCKED_EXTERNAL_ACCOUNT` nos testes opt-in; isso é skip explícito, não aprovação. Erros transitórios continuam falhando se esgotarem as tentativas.

Mensagens são sanitizadas antes de log/benchmark. Nunca entram chave, `Authorization`, prompt integral, currículo integral ou vaga integral.
