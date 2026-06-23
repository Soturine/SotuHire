# Arquitetura frontend-ready

## Direção

```text
Frontend moderno / apps/web
        -> API Contract
        -> FastAPI local /api/v1
        -> Core Python modules
```

O frontend moderno em `apps/web` é a experiência local principal desde a v1.4.0. O Streamlit
continua disponível como modo legado/dev/local debug, consumindo o core sem remover o fluxo
existente.

## Responsabilidades do frontend

- layout, navegação e páginas;
- animações, responsividade e componentes;
- cards, tabelas, gráficos e estados visuais;
- chamadas HTTP para a API;
- validação leve de campos obrigatórios;
- apresentação de loading, erro, vazio e sucesso;
- organização de fluxos como upload, análise, revisão e Kanban.

## Responsabilidades do backend/core

- extração de currículo e vaga;
- IA opcional e fallback local;
- Análise de Compatibilidade, scoring e confiança;
- ATS review e Resume Tailor;
- GitHub Analyzer e evidências de portfolio;
- tracker, histórico e persistência;
- configurações locais de IA e armazenamento backend-side de segredos;
- privacidade, storage local e políticas de retenção;
- regras anti-invenção;
- validação forte de payloads;
- normalização, deduplicação e cálculo de métricas.

## Fronteira de segurança

O frontend não deve receber API keys, Gemini keys, GitHub tokens ou segredos locais. A seção
**IA e Providers** envia a chave apenas para `/api/v1/settings/ai`; a API nunca devolve a chave. A
API HTTP para o frontend usa CORS restrito e deve ser configurada para origens conhecidas. O GitHub
Pages continua estático e não executa backend.

## Modo recomendado de evolução

1. Rodar o fluxo web-first com `.\start-sotuhire.ps1`.
2. Em modo manual, rodar a API com `python scripts/run_api.py` e o app com `cd apps/web && npm run dev`.
3. Usar Modo Demo para navegar com dados fictícios.
4. Usar Modo API Real para consumir `/api/v1`.
5. Manter os cálculos e regras críticas no core Python.
