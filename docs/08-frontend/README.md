# Frontend-ready handoff

Esta pasta prepara o SotuHire para um frontend profissional futuro, feito com Lovable,
React, Vite, Next.js ou outro stack moderno.

O frontend pode ser redesenhado livremente. Layout, navegação, animações, cards,
responsividade, gráficos e componentes são responsabilidade da experiência visual futura.

O backend, a API e o core não devem ser reinventados no frontend. Matching, scores,
ATS, Resume Tailor, GitHub Analyzer, validações fortes, privacidade e regras
anti-invenção continuam no core Python e em uma futura camada de API.

## Como usar esta pasta

- Use [frontend-architecture.md](frontend-architecture.md) para entender as responsabilidades.
- Use [lovable-handoff.md](lovable-handoff.md) como briefing para Lovable ou outro gerador visual.
- Use [screen-map.md](screen-map.md) para mapear telas sem prender layout.
- Use [api-contract.md](api-contract.md) para contratos HTTP futuros.
- Use [mock-data-contract.md](mock-data-contract.md) e `docs/assets/mock-api/` para prototipar.
- Use [frontend-rules.md](frontend-rules.md) para limites que a UI não pode quebrar.
- Use [application-intelligence.md](application-intelligence.md) para analytics do Kanban/tracker.

## Regra central

Lovable pode criar a interface. Lovable não deve criar a verdade de negócio.

O frontend deve consumir contratos, exibir estados e pedir ações. O core deve decidir
score, evidência, segurança, persistência e recomendações.

