# Prompt Catalog

Este documento é o índice dos prompts oficiais planejados para o SotuHire.

Os prompts completos ficam em `docs/04-ai/prompts/`.

## Regra principal

Não usar prompt genérico para tudo.

Cada função do produto deve ter prompt próprio, saída estruturada e schema validável.

## Prompts

| Prompt | Arquivo | Função |
|---|---|---|
| Resume Extraction v1 | `prompts/resume-extraction-v1.md` | Extrair currículo bruto para perfil estruturado. |
| Job Extraction Multi-Domain v1 | `prompts/job-extraction-multi-domain-v1.md` | Extrair vaga de qualquer área para requisitos estruturados. |
| Domain Classification v1 | `prompts/domain-classification-v1.md` | Classificar domínio profissional e categorias. |
| Match Analysis Evidence-Based v1 | `prompts/match-analysis-evidence-based-v1.md` | Comparar perfil e vaga por evidências. |
| ATS Analysis v1 | `prompts/ats-analysis-v1.md` | Avaliar currículo para ATS e clareza. |
| Resume Tailor v1 | `prompts/resume-tailor-v1.md` | Sugerir adaptação segura do currículo. |
| GitHub Repo Analysis v2 | `prompts/github-repo-analysis-v2.md` | Avaliar repositório como evidência técnica e profissional. |
| GitHub Profile Analysis v1 | `prompts/github-profile-analysis-v1.md` | Avaliar perfil GitHub agregado. |
| Portfolio Gap Analysis v1 | `prompts/portfolio-gap-analysis-v1.md` | Identificar lacunas de portfólio. |
| Hidden Job Detection v1 | `prompts/hidden-job-detection-v1.md` | Detectar oportunidade em texto informal. |
| Career Advice v1 | `prompts/career-advice-v1.md` | Gerar plano de evolução profissional. |

## Regras globais

Todos os prompts devem obedecer:

- retornar JSON válido;
- não usar Markdown na resposta;
- não inventar fatos;
- usar `null` ou array vazio quando não houver evidência;
- retornar confidence por campo importante;
- diferenciar ausente de não analisado;
- marcar necessidade de revisão humana quando necessário;
- não gerar afirmações profissionais sem evidência.

## Status

| Prompt | Status documental | Status código |
|---|---|---|
| Resume Extraction | planejado | não implementado |
| Job Extraction | planejado | não implementado |
| Domain Classification | planejado | não implementado |
| Match Analysis | planejado | não implementado |
| ATS Analysis | planejado | não implementado |
| Resume Tailor | planejado | não implementado |
| GitHub Repo Analysis | planejado | não implementado |
| GitHub Profile Analysis | planejado | não implementado |
| Portfolio Gap Analysis | planejado | não implementado |
| Hidden Job Detection | planejado | não implementado |
| Career Advice | planejado | não implementado |

## Como usar este catálogo

- Para visão geral, leia este arquivo.
- Para arquitetura, leia `prompt-architecture.md`.
- Para registro e versionamento, leia `prompt-registry.md`.
- Para implementar, use os arquivos individuais em `prompts/`.
