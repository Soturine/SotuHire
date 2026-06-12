# Implementação do MVP Core

Este documento define a ordem de implementação para evitar overengineering.

## Ordem recomendada

1. Schemas Pydantic.
2. Parser simples de currículo PDF/TXT.
3. Parser simples de vaga colada.
4. Opportunity Fit Score determinístico.
5. Resume Tailor em modo sugestão.
6. Análise Gemini com structured output.
7. Streamlit simples.
8. SQLite.
9. Kanban.
10. Extensão assistiva.

## Branch sugerida

```bash
git checkout -b feat/mvp-core-schemas
```

## Arquivos principais

```text
modules/schemas/job_analysis.py
modules/schemas/user_preferences.py
modules/schemas/resume_tailor.py
modules/preferences/opportunity_fit.py
modules/resume_tailor/tailor_rules.py
tests/test_opportunity_fit.py
tests/test_resume_tailor.py
```

## O que não fazer agora

- PyTorch;
- agente complexo;
- auto-apply;
- scraping logado;
- extensão antes da análise local;
- DOCX antes do Markdown revisável.

## Atualização v0.1

A implementação consolidada da versão inicial está descrita em [MVP v0.1 Implementation](mvp-v0.1-implementation.md). O núcleo agora prioriza texto colado, scores determinísticos, Pydantic, Streamlit e testes antes de integrações externas.

O arquivo atual permanece como histórico da ordem de implementação e referência para evoluções posteriores.
