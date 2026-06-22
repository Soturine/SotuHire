# Future web frontend

Este diretório é reservado para o futuro frontend moderno do SotuHire.

Ele pode ser criado com Lovable, React, Vite, Next.js ou outro stack. A v1.1.0 não cria
um app web completo; ela prepara contratos, mocks e regras para esse trabalho.

O frontend deve seguir:

- `docs/08-frontend/api-contract.md`;
- `docs/08-frontend/mock-data-contract.md`;
- `docs/08-frontend/screen-map.md`;
- `docs/08-frontend/frontend-rules.md`;
- mocks em `docs/assets/mock-api/`.

O frontend pode redesenhar a experiência visual livremente, mas não deve implementar regra
de negócio crítica. Match Score, ATS, Resume Tailor, GitHub Analyzer, validações fortes e
regras anti-invenção pertencem ao backend/core.

O Streamlit continua sendo o app local atual/dev enquanto a camada web moderna não existir.

