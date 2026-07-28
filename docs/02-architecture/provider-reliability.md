# Confiabilidade de providers

Gemini e OpenAI compartilham o contrato `ProviderError`, política pequena de retry e observabilidade sanitizada. Cada tentativa registra provider/modelo, status, código, categoria, retryability, `Retry-After`, request ID, mensagem sanitizada, tentativa e horário; chave, cabeçalho de autorização e conteúdo pessoal integral não são persistidos.

Os adapters usam structured output nativo. O schema Gemini é sanitizado para o subconjunto aceito; OpenAI usa o contrato estruturado do endpoint Responses. Resposta vazia, truncada, bloqueada por safety ou inválida não recebe defaults silenciosos.

Retry ocorre apenas para erros transitórios, respeita `Retry-After`, inclui jitter e termina no máximo configurado. Quota e faturamento não são repetidos imediatamente. O reparo de schema aceita uma resposta original e no máximo uma tentativa, marca `repaired`/`repair_reason` e não pode criar fatos ausentes.

Fallback é explícito por `provider_requested`, `provider_used`, modelos solicitado/usado, `fallback_used`, `fallback_reason` e `degraded_mode`. A UI não apresenta demo como execução real.

As suites `provider-diagnostic`, `provider-structured-output`, `release-smoke`, `schema-repair` e `fallback` vivem no runner de benchmarks. Resultados externos são opt-in e nunca tornam o CI público dependente de contas pagas.
