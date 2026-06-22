# Arquitetura frontend-ready

## Direção

```text
Frontend moderno / Lovable
        -> API Contract
        -> Local API / Future API Layer
        -> Core Python modules
```

O Streamlit continua sendo o app local atual. A v1.1.0 apenas prepara a transição para
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
Quando existir uma API HTTP para o frontend, CORS deve ser restrito e configurado para
origens conhecidas. O GitHub Pages continua estático e não executa backend.

## Modo recomendado de evolução

1. Prototipar telas com os mocks oficiais.
2. Validar navegação e estados visuais sem backend real.
3. Implementar uma camada de API versionada.
4. Trocar mocks por chamadas reais.
5. Manter os cálculos e regras críticas no core Python.

