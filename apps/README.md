# Apps

Este diretório concentra entrypoints de aplicação do SotuHire.

Na v1.2.0, o app local atual continua sendo o Streamlit na raiz do projeto e `apps/api`
fornece a FastAPI local em `/api/v1`. O diretório `apps/web` é reservado para um frontend moderno
futuro, criado com Lovable, React, Vite, Next.js ou outro stack compatível.

Regras:

- não mover regra de negócio crítica para o frontend;
- não colocar API keys, tokens ou dados sensíveis em apps públicos;
- consumir contratos definidos em `docs/08-frontend/`;
- usar `apps/api` como ponte HTTP, sem duplicar regra do core;
- manter o core Python como fonte de verdade para matching, ATS, Tailor, GitHub Analyzer,
  tracker e validações fortes.
