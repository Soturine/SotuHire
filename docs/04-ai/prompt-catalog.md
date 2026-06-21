# Prompt Catalog

Este documento é o índice dos prompts oficiais planejados para o SotuHire.

Os prompts completos ficam em `docs/04-ai/prompts/`.

O objetivo deste catálogo é evitar prompts soltos, curtos ou genéricos demais. Cada prompt precisa ter uma função clara, contrato de entrada, contrato de saída, regras anti-invenção, critérios de confiança e relação explícita com os módulos que o Codex deverá implementar nas próximas versões.

## Decisão de arquitetura

O SotuHire não deve usar um prompt único para currículo, vaga, ATS, matching, GitHub e carreira.

O produto deve usar uma camada de prompts versionados, separados por tarefa, com schemas próprios e validação posterior no código.

A regra é:

```txt
IA interpreta, extrai, classifica, explica e sugere.
Código valida, calcula score, aplica regras, persiste dados e bloqueia exageros.
```

Isso mantém o produto mais testável, menos frágil e mais seguro para uso com currículos, vagas e evidências profissionais.

## Regra principal

Não usar prompt genérico para tudo.

Cada função do produto deve ter prompt próprio, saída estruturada e schema validável.

Cada prompt deve ser tratado como contrato de produto, não como texto improvisado dentro de uma função Python.

## Prompts oficiais planejados

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

## Regras globais para todos os prompts

Todos os prompts devem obedecer:

- retornar JSON válido;
- não usar Markdown na resposta do modelo;
- não usar bloco de código na resposta do modelo;
- não inventar fatos;
- não inventar experiência profissional;
- não inventar empresa, salário, curso, certificação, registro profissional ou resultado;
- usar `null` ou array vazio quando não houver evidência;
- retornar `confidence` por campo importante;
- diferenciar informação ausente de informação não analisada;
- marcar necessidade de revisão humana quando necessário;
- não gerar afirmações profissionais sem evidência;
- preservar a diferença entre sugestão e fato comprovado;
- preservar a diferença entre competência comprovada e competência inferida;
- preservar a diferença entre requisito obrigatório, desejável e opcional;
- não transformar projeto pessoal em experiência corporativa;
- não transformar curso livre em graduação;
- não transformar conhecimento citado em certificação;
- não afirmar registro profissional se ele não estiver no currículo;
- não sugerir mentira curricular;
- quando houver dúvida, reduzir confidence.

## Campos mínimos de entrada

Sempre que possível, os prompts devem receber contexto estruturado em vez de texto solto.

Campos comuns:

```json
{
  "prompt_id": "string",
  "prompt_version": "string",
  "language": "pt-BR",
  "analysis_mode": "fast | standard | deep",
  "user_goal": "string | null",
  "candidate_profile": "object | null",
  "job_post": "object | null",
  "resume_text": "string | null",
  "job_text": "string | null",
  "portfolio_evidence": "object | null",
  "github_evidence": "object | null",
  "memory_context": "object | null",
  "constraints": "object | null"
}
```

Nem todo prompt usa todos esses campos, mas o padrão ajuda o Codex a implementar um `PromptRegistry` consistente.

## Campos mínimos de saída

Sempre que possível, a saída deve conter:

```json
{
  "prompt_id": "string",
  "prompt_version": "string",
  "result": {},
  "confidence": 0.0,
  "needs_human_review": true,
  "warnings": [],
  "evidence": [],
  "missing_information": [],
  "model_notes": []
}
```

Os prompts específicos podem expandir esse formato com schemas próprios.

## Status documental e técnico

| Prompt | Status documental | Status código | Marco |
|---|---|---|---|
| Resume Extraction | implementado | implementado | v0.10.0 |
| Job Extraction | implementado | implementado | v0.10.0 |
| Domain Classification | implementado | implementado | v0.10.0 |
| Match Analysis | planejado | não implementado | v0.12.0 |
| ATS Analysis | planejado | não implementado | v0.12.0 |
| Resume Tailor | planejado | não implementado | v0.12.0 |
| GitHub Repo Analysis | implementado | implementado | v0.11.0 |
| GitHub Profile Analysis | revisado | fallback heurístico existente | v0.11.0 |
| Portfolio Gap Analysis | revisado | planejamento/futuro | v0.11.0 |
| Hidden Job Detection | planejado | não implementado | pós-v0.10.0 |
| Career Advice | planejado | não implementado | v0.12.0/v1.0 |

## Como o Codex deve usar estes documentos

O Codex deve ler primeiro:

1. `docs/04-ai/prompt-architecture.md`;
2. `docs/04-ai/prompt-registry.md`;
3. este catálogo;
4. o arquivo específico do prompt a implementar;
5. o roadmap da versão alvo.

A implementação não deve colocar prompts grandes diretamente no meio de funções de análise.

A implementação deve criar uma camada de registro, validação e versionamento.

## Sequência recomendada de implementação

1. Criar tipos base de prompt.
2. Criar `PromptSpec`.
3. Criar `PromptRegistry`.
4. Criar `JsonGuard`.
5. Criar schemas Pydantic por prompt.
6. Implementar prompt de extração de currículo.
7. Implementar prompt de extração de vaga.
8. Implementar prompt de classificação de domínio.
9. Adicionar testes com provider fake.
10. Só depois conectar ao provider real.

## Como lidar com heurística existente

As heurísticas atuais não devem ser apagadas na primeira implementação.

Elas devem virar fallback e mecanismo de comparação.

Fluxo ideal:

```txt
heurística local -> extração inicial rápida
IA estruturada -> extração semântica profunda
merger -> escolhe campos, confidence e revisão humana
código -> valida e persiste
```

## Critérios de pronto para prompts

Um prompt só é considerado pronto quando:

- tem arquivo próprio em `docs/04-ai/prompts/`;
- tem `PROMPT_ID`;
- tem `PROMPT_VERSION`;
- tem objetivo claro;
- tem quando usar;
- tem quando não usar;
- tem input contract;
- tem output schema;
- tem regras anti-invenção;
- tem regras de confidence;
- tem failure modes;
- tem relação com módulos de código;
- tem pelo menos uma fixture planejada;
- tem teste planejado com provider fake.

## Relação com roadmap

Os prompts não são todos implementados de uma vez.

A ordem segue os marcos:

- v0.10.0: currículo, vaga e domínio;
- v0.11.0: GitHub, perfil GitHub e portfólio;
- v0.12.0: matching, ATS, tailor e carreira;
- v1.0: consolidação, exemplos multiárea e demos.

## Relação com multiárea

Todos os prompts devem evitar viés exclusivo para tecnologia.

Eles precisam funcionar para:

- tecnologia;
- cybersecurity;
- engenharia biomédica;
- engenharia civil;
- outras engenharias;
- enfermagem;
- psicologia;
- pedagogia;
- arquitetura;
- design de interiores;
- administração;
- marketing;
- financeiro;
- cursos técnicos;
- saúde;
- educação;
- humanas;
- exatas;
- indústria;
- áreas generalistas.

## Como revisar alterações futuras

Quando um prompt mudar, revisar:

- se o schema mudou;
- se os testes precisam mudar;
- se a versão do prompt precisa subir;
- se outputs antigos continuam compatíveis;
- se o changelog precisa citar a mudança;
- se a documentação da versão alvo continua coerente.

## Como usar este catálogo

- Para visão geral, leia este arquivo.
- Para arquitetura, leia `prompt-architecture.md`.
- Para registro e versionamento, leia `prompt-registry.md`.
- Para implementar, use os arquivos individuais em `prompts/`.
- Para saber prioridade, leia `docs/01-product/roadmap.md`.
- Para entender o produto, leia `docs/01-product/vision.md`.
