# Human-Approved Career Copilot

`CareerCopilot` recebe intenção, lê contexto mínimo, seleciona uma tool allowlisted, cria plano e
produz `ProposedAction`. Ele não escreve repositories diretamente antes de aprovação.

```text
Intent → Career State → Plan → Proposal → Preview → Approval → Execute → Audit → Undo
```

Propostas expiram e possuem dependency hash. Mudança relevante torna a proposta stale. Replay é
contido por idempotency key. Documento, README ou vaga nunca pode acionar uma tool.

