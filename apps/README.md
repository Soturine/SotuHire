# Apps

Este diretório reserva espaço para aplicações futuras do SotuHire.

Na v1.1.0, o app local atual continua sendo o Streamlit na raiz do projeto. O diretório
`apps/web` é reservado para um frontend moderno futuro, criado com Lovable, React, Vite,
Next.js ou outro stack compatível.

Regras:

- não mover regra de negócio crítica para o frontend;
- não colocar API keys, tokens ou dados sensíveis em apps públicos;
- consumir contratos definidos em `docs/08-frontend/`;
- manter o core Python como fonte de verdade para matching, ATS, Tailor, GitHub Analyzer,
  tracker e validações fortes.

