# Catálogo de Prompts

## Objetivo

Este documento é o índice dos prompts planejados para o SotuHire.

Os prompts completos ficam em:

```txt
docs/04-ai/prompts/
```

A intenção é evitar um único documento gigante, incompleto e difícil de manter.

## Filosofia

Os prompts do SotuHire devem ser:

- separados por função;
- versionados;
- testáveis;
- compatíveis com JSON estruturado;
- validados por schema;
- focados em evidência;
- multiárea;
- seguros contra invenção;
- compatíveis com múltiplos providers.

## Lista de prompts

| Prompt | Arquivo | Versão alvo | Objetivo |
|---|---|---:|---|
| Resume Extraction | `prompts/resume-extraction-v1.md` | v0.10 | Extrair currículo em JSON estruturado. |
| Job Extraction Multi-Domain | `prompts/job-extraction-multi-domain-v1.md` | v0.10 | Extrair vaga de qualquer área em JSON. |
| Domain Classification | `prompts/domain-classification-v1.md` | v0.10 | Classificar domínio profissional e requisitos. |
| Match Analysis Evidence-Based | `prompts/match-analysis-evidence-based-v1.md` | v0.12 | Comparar perfil e vaga com evidências. |
| ATS Analysis | `prompts/ats-analysis-v1.md` | v0.12 | Avaliar currículo para ATS sem inventar fatos. |
| Resume Tailor | `prompts/resume-tailor-v1.md` | v0.12 | Sugerir adaptação segura do currículo. |
| GitHub Repo Analysis | `prompts/github-repo-analysis-v2.md` | v0.11 | Avaliar repositório como evidência técnica e profissional. |
| GitHub Profile Analysis | `prompts/github-profile-analysis-v1.md` | v0.11 | Avaliar perfil GitHub como portfólio. |
| Portfolio Gap Analysis | `prompts/portfolio-gap-analysis-v1.md` | v0.11 | Identificar lacunas no portfólio para objetivos de carreira. |
| Hidden Job Detection | `prompts/hidden-job-detection-v1.md` | v0.10+ | Detectar oportunidades em textos públicos/postagens. |
| Career Advice | `prompts/career-advice-v1.md` | v0.12 | Gerar plano de evolução profissional com base em evidências. |

## Regras globais

Todos os prompts devem conter estas regras:

1. Retornar somente JSON válido quando o prompt for estruturado.
2. Não usar markdown dentro da resposta JSON.
3. Não inventar fatos.
4. Usar `null`, array vazio ou `not_evidenced` quando a informação não estiver presente.
5. Diferenciar ausência de dado de dado não analisado.
6. Atribuir confidence por campo importante.
7. Incluir evidência sempre que possível.
8. Marcar campos que precisam de revisão humana.
9. Não sugerir mentir, exagerar ou inventar experiência.
10. Tratar credenciais profissionais como sensíveis.

## Relação com v0.10, v0.11 e v0.12

### v0.10.0

Foco em extração estruturada:

- Resume Extraction;
- Job Extraction;
- Domain Classification;
- Hidden Job Detection inicial.

### v0.11.0

Foco em GitHub e portfólio:

- GitHub Repo Analysis;
- GitHub Profile Analysis;
- Portfolio Gap Analysis.

### v0.12.0

Foco em matching e recomendações:

- Match Analysis;
- ATS Analysis;
- Resume Tailor;
- Career Advice.

## Relação com código

Documentação de prompts deve virar código em:

```txt
modules/ai/prompts/
modules/ai/schemas/
modules/ai/prompt_registry.py
modules/ai/json_guard.py
```

## Qualidade esperada

Um prompt só está pronto quando possui:

- input contract;
- output schema;
- system prompt;
- user prompt template;
- calibration rules;
- confidence rules;
- anti-fabrication rules;
- failure modes;
- fixtures de teste;
- módulos relacionados.
