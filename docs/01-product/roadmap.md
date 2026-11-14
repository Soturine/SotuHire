# Roadmap pós-v2

## Estado atual

V2 conecta Evidence Graph, portfólio, Career State, Next Best Actions, Copilot, approval, audit e
undo. O escopo vigente está em [current-product-scope](current-product-scope.md) e a implementação
em [v2.0](../07-development/v2.0-implementation.md).

## Próximos investimentos orientados por evidência

- medir acceptance/edit/rejection/stale/undo com `n`, sem causalidade;
- completar strings históricas pt-BR/en-US e auditoria WCAG por feedback real;
- reduzir stores de compatibilidade após migração comprovada e reversível;
- melhorar criação/merge visual do graph e exports locais de portfólio;
- avaliar plugins/connectors e MCP somente com transporte, token, scopes e audit completos.
- fechar as pendências da [auditoria de 2026-11](../00-audit/2026-11-independent-assurance-audit.md):
  validação de afirmações no ponto de aceite, lockfile Python, migração para zod 4, módulos
  inalcançáveis listados na [triagem](../00-audit/2026-11-dead-dedupe-triage.md) e
  Firefox/WebKit fora do CI.

Não há versão artificial prometida. Continuam fora: auto-apply, login, envio, CAPTCHA e decisões
críticas autônomas.
