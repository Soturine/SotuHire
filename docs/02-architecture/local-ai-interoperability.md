# Interoperabilidade com IA local

## Boundary

`modules/ai/local_interop.py` fornece adapters OpenAI-compatible para Ollama, LM Studio e um
endpoint compatível escolhido pelo usuário. Os defaults são, respectivamente,
`127.0.0.1:11434/v1`, `127.0.0.1:1234/v1` e `127.0.0.1:8000/v1`.

- nenhuma descoberta de rede ou varredura de portas ocorre;
- somente loopback é aceito por padrão;
- endpoint remoto exige opt-in avançado, HTTPS e o transporte SSRF-safe;
- userinfo, query e fragment são recusados;
- `/models` só é consultado quando o usuário aciona o health check;
- respostas têm timeout, limite de bytes e contrato JSON;
- chave opcional fica no backend e nunca é retornada pela API.

## Contratos

| Endpoint | Efeito |
| --- | --- |
| `GET /api/v1/ai/local/defaults` | lista defaults; não faz probe |
| `POST /api/v1/ai/local/health` | consulta somente o endpoint submetido |
| `GET /api/v1/ai/local/routing` | expõe a matriz task/provider |

O adapter usa `/chat/completions` com `response_format=json_schema`, temperatura zero e validação
Pydantic. “Unverified” na matriz significa que o protocolo é suportado, mas não houve benchmark
real daquele provider/modelo; não equivale a aprovação de qualidade.

