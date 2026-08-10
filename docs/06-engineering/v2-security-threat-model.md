# Threat model v2

| Superfície | Ameaça | Controle |
| --- | --- | --- |
| Copilot tools | tool/approval injection | registry fechado, schema, approval e status CAS |
| Documentos/web | prompt injection | conteúdo tratado como dado; sem autoridade de tool |
| Propostas | replay/stale | idempotency key, dependency hash, expiry |
| Attachments | path/arquivo malicioso | metadata/hash, tamanho, paths locais confinados |
| Links/portfolio | SSRF/phishing | URL validada; fetch usa transporte SSRF-safe existente |
| Busca | query injection | parâmetros SQLite, limite e escaping LIKE |
| Provider context | exfiltração | opt-in, purpose, budget, sensitive omission |
| MCP | escopo excessivo | não exposto na v2.0; exige loopback/token/scopes/audit |

Não existem tools para submit, e-mail, login, sessão, cookie, CAPTCHA, pagamento ou delete profile.

