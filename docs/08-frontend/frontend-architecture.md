# Arquitetura frontend-ready

## Direção

```text
Frontend moderno / Lovable
        -> API Contract
        -> FastAPI local /api/v1
        -> Core Python modules
```

O Streamlit continua sendo o app local atual. A v1.2.0 adiciona a FastAPI local para
um frontend moderno separado, sem remover o fluxo existente.

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
- matching, scoring e confidence;
- ATS review e Resume Tailor;
- GitHub Analyzer e evidências de portfolio;
- tracker, histórico e persistência;
- privacidade, storage local e políticas de retenção;
- regras anti-invenção;
- validação forte de payloads;
- normalização, deduplicação e cálculo de métricas.

## Fronteira de segurança

O frontend não deve receber API keys, Gemini keys, GitHub tokens ou segredos locais.
A API HTTP para o frontend usa CORS restrito e deve ser configurada para
origens conhecidas. O GitHub Pages continua estático e não executa backend.

## Modo recomendado de evolução

1. Prototipar telas com os mocks oficiais.
2. Validar navegação e estados visuais sem backend real.
3. Usar `python scripts/run_api.py` para subir a API local.
4. Trocar mocks por chamadas reais em `/api/v1`.
5. Manter os cálculos e regras críticas no core Python.
