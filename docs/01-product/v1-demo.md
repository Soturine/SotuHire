# Demo v1.0.0

## Objetivo

A demo v1.0.0 mostra o SotuHire como plataforma local-first de inteligência de carreira multiárea.
Todos os dados são fictícios.

## Cenários cobertos

| Área | Currículo | Vaga | Output estático |
|---|---|---|---|
| Backend | `examples/demo_resume_dev_backend.md` | `examples/demo_job_dev_backend.md` | `examples/outputs/match_dev_backend.md` |
| Enfermagem | `examples/demo_resume_enfermagem.md` | `examples/demo_job_enfermeiro_uti.md` | `examples/outputs/match_enfermagem.md` |
| Pedagogia | `examples/demo_resume_pedagogia.md` | `examples/demo_job_professor_fundamental.md` | `examples/outputs/match_pedagogia.md` |
| Engenharia civil | `examples/demo_resume_engenharia_civil.md` | `examples/demo_job_engenheiro_civil_obras.md` | `examples/outputs/match_engenharia_civil.md` |
| Arquitetura | `examples/demo_resume_arquitetura.md` | `examples/demo_job_arquiteto_interiores.md` | `examples/outputs/match_arquitetura.md` |
| Cybersecurity | `examples/demo_resume_cybersecurity.md` | `examples/demo_job_analista_soc.md` | `examples/outputs/match_cybersecurity.md` |

## Como rodar uma demo no app local

1. Inicie o app com `streamlit run app.py`.
2. Abra o modo rápido ou avançado.
3. Cole um currículo fictício de `examples/demo_resume_*.md`.
4. Cole a vaga fictícia correspondente de `examples/demo_job_*.md`.
5. Rode a análise.
6. Revise Match Score, Confidence, Evidence Score, gaps críticos e safe actions.

## O que observar

- Backend: evidências técnicas e GitHub/portfolio ajudam no match.
- Enfermagem: COREN e formação são requisitos sensíveis.
- Pedagogia: BNCC, etapa escolar e formação pesam mais.
- Engenharia civil: CREA, obra, AutoCAD/Revit e cronograma são centrais.
- Arquitetura: CAU, portfolio, projeto executivo e software visual são relevantes.
- Cybersecurity: SIEM/SOC contam, mas senioridade e evidências técnicas precisam ser explícitas.

## Limites da demo

- Os outputs estáticos são exemplos de apresentação, não resultados gerados em tempo real pelo site.
- GitHub Pages não roda o backend.
- Os dados são fictícios e não devem ser usados como currículo real.
