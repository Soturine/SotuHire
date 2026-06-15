# Roadmap

## Estado atual

A versão atual do SotuHire é a v0.9.0.

Ela já deve ser tratada como uma base de produto ampla, não como MVP inicial.

A v0.9.0 já inclui:

- análise local de currículo e vaga;
- Match Score;
- ATS Score;
- Opportunity Fit Score;
- Risk Score;
- Resume Tailor;
- tracker de candidaturas;
- dashboard;
- Career Memory;
- RAG lexical local;
- perfil profissional persistente;
- Search Intelligence;
- Hidden Jobs Radar;
- extensão assistiva;
- Local Companion API;
- análise inicial de GitHub e portfólio;
- Gemini opcional;
- documentação ampla;
- testes automatizados;
- workflows de qualidade e documentação.

O foco agora não é provar que o projeto existe. O foco é tornar o projeto mais coerente, mais generalista, mais confiável e mais fácil de evoluir.

## Diagnóstico pós-v0.9.0

A auditoria da v0.9.0 mostrou três pontos principais:

1. A documentação cresceu, mas precisava ser reorganizada para não misturar visão antiga, roadmap antigo e planos novos no mesmo fluxo de leitura.
2. O produto já fala em multiárea, mas o código atual ainda tem partes enviesadas para tecnologia, especialmente parsers, skills e matching.
3. A IA existe, mas ainda não usa um sistema completo de prompts versionados, schemas ricos, confidence por campo, Prompt Registry e validação forte.

A v0.9.1 deve corrigir documentação e preparar o terreno para o Codex implementar os próximos módulos.

## Princípios do roadmap

### Current-first

Documentos principais devem começar pelo estado atual do produto e só depois mostrar histórico.

### Sem prometer o que ainda não está implementado

Cada etapa deve separar:

- entregue;
- planejado;
- experimental;
- fora de escopo.

### IA com contrato

IA não deve ser chamada com prompt solto.

Cada função deve ter:

- prompt_id;
- prompt_version;
- input contract;
- output schema;
- regras anti-invenção;
- confidence rules;
- failure modes;
- testes.

### Multiárea por design

O sistema deve funcionar para tecnologia, engenharias, saúde, educação, humanas, arquitetura, design, indústria, cursos técnicos e outras áreas.

A solução deve ser baseada em domínio, categoria de requisito, evidência e confiança, não em listas fixas de palavras de TI.

## Linha do tempo planejada

| Versão | Tema | Objetivo principal |
|---|---|---|
| v0.9.1 | Docs & Prompt Reorganization | Reorganizar roadmap, visão e prompts para ficarem prontos para implementação. |
| v0.10.0 | AI Structured Extraction + Domain Intelligence | Usar IA estruturada para extrair currículo/vaga e classificar domínios multiárea. |
| v0.11.0 | GitHub Analyzer 2.0 | Evoluir análise de GitHub para GitHub API, árvore completa, sampler, prompt estruturado e evidências. |
| v0.12.0 | Match Engine 2.0 | Substituir matching simples por compatibilidade baseada em requisitos, evidências, domínio e confiança. |
| v1.0 | Generalist Career Intelligence Platform | Fechar uma versão estável, demonstrável e multiárea. |

---

# v0.9.1 — Documentation & Prompt Reorganization

## Objetivo

Transformar a documentação em uma base clara para implementação com Codex.

A v0.9.1 não é uma versão de feature nova em código. Ela é uma versão de alinhamento documental e planejamento técnico.

## Entra na v0.9.1

### Produto

- Reescrever `docs/01-product/vision.md` como visão atual-first.
- Reescrever `docs/01-product/roadmap.md` como roadmap atual-first.
- Criar `docs/01-product/roadmap-history.md` para histórico antigo.
- Manter `docs/01-product/multi-domain-product-strategy.md` como estratégia de domínio.

### IA

- Transformar `docs/04-ai/prompt-catalog.md` em índice.
- Criar `docs/04-ai/prompt-architecture.md`.
- Criar `docs/04-ai/prompt-registry.md`.
- Criar pasta `docs/04-ai/prompts/`.
- Separar os prompts em arquivos próprios.

### Prompts separados

- `resume-extraction-v1.md`;
- `job-extraction-multi-domain-v1.md`;
- `domain-classification-v1.md`;
- `match-analysis-evidence-based-v1.md`;
- `ats-analysis-v1.md`;
- `resume-tailor-v1.md`;
- `github-repo-analysis-v2.md`;
- `github-profile-analysis-v1.md`;
- `portfolio-gap-analysis-v1.md`;
- `hidden-job-detection-v1.md`;
- `career-advice-v1.md`.

### MkDocs

- Atualizar navegação para refletir a nova estrutura.

### Changelog

- Registrar a reorganização documental.

## Não entra na v0.9.1

- Código novo.
- Alterações em parsers.
- Alterações em matching.
- Alterações na extensão.
- Alterações em coleta autenticada.
- Alterações em infraestrutura.

## Critérios de pronto

- Roadmap não começa mais em v0.4.
- Vision não trata TI/dev como limite do produto.
- Histórico fica separado do plano atual.
- Prompt catalog vira índice.
- Cada prompt principal tem documento próprio.
- MkDocs referencia os novos documentos.
- Não há alteração de código.

---

# v0.10.0 — AI Structured Extraction + Domain Intelligence

## Objetivo

Adicionar uma camada de extração estruturada com IA para currículo e vaga, com validação por schema, confidence por campo e classificação multiárea.

O objetivo não é substituir totalmente parsers heurísticos. O objetivo é criar um pipeline híbrido:

```txt
parser local
+ IA estruturada
+ validação Pydantic
+ confidence merger
+ revisão humana
```

## Problemas que a v0.10 resolve

- Parser heurístico enviesado para TI.
- Skills pouco normalizadas fora de tecnologia.
- Vagas multiárea difíceis de interpretar.
- Falta de confidence por campo.
- Falta de distinção clara entre requisito obrigatório, desejável e incerto.
- Falta de classificação de credenciais profissionais, ferramentas, equipamentos, normas e ambientes.

## Módulos planejados

```txt
modules/ai/
  prompt_registry.py
  json_guard.py
  model_router.py
  confidence.py
  schemas/
    resume_extraction.py
    job_extraction.py
    domain_classification.py

modules/domain_intelligence/
  classifier.py
  catalog_loader.py
  requirement_classifier.py
  skill_taxonomy.py
  domain_rules.py
  transferable_skills.py
```

## Funcionalidades

### Extração de currículo com IA

A IA deve receber texto extraído do currículo e retornar JSON estruturado com:

- identidade;
- resumo profissional;
- domínios profissionais;
- senioridade estimada;
- formação;
- experiências;
- skills;
- ferramentas;
- certificações;
- registros profissionais;
- idiomas;
- projetos;
- lacunas ATS;
- campos de baixa confiança.

### Extração de vaga com IA

A IA deve receber texto de vaga e retornar JSON estruturado com:

- título;
- empresa;
- fonte;
- localização;
- modalidade;
- contrato;
- salário quando informado;
- domínio primário e secundário;
- senioridade;
- requisitos obrigatórios;
- requisitos desejáveis;
- responsabilidades;
- benefícios;
- palavras-chave ATS;
- red flags;
- campos ausentes.

### Domain Intelligence

O sistema deve classificar requisitos por categoria:

- formação;
- hard skill;
- soft skill;
- ferramenta;
- software;
- equipamento;
- certificação;
- registro profissional;
- idioma;
- experiência;
- metodologia;
- norma;
- responsabilidade;
- disponibilidade;
- localização;
- portfólio;
- outro.

### Áreas regulamentadas

O sistema deve identificar requisitos como:

- COREN;
- CRP;
- CREA;
- CAU;
- CFT;
- OAB;
- CRC;
- CRF;
- CRM.

E deve tratar esses requisitos como sensíveis, sem sugerir que sejam adicionados caso não estejam evidenciados.

## Prompts usados

- `resume_extraction_v1`;
- `job_extraction_multi_domain_v1`;
- `domain_classification_v1`.

## Critérios de pronto

- IA retorna JSON validado por Pydantic.
- Campos têm confidence.
- Parser heurístico continua funcionando como fallback.
- Sistema consegue processar exemplos de pelo menos cinco áreas diferentes.
- Campos incertos aparecem para revisão humana.
- Não há recomendação para inventar credenciais ou experiências.

---

# v0.11.0 — GitHub Analyzer 2.0

## Objetivo

Transformar a análise de GitHub em uma análise profunda, baseada em evidências e conectada ao currículo e às vagas.

A v0.11 deve aproximar o nível técnico da análise do REPOLOGS, mas com foco diferente: o SotuHire não avalia só qualidade de repositório. Ele avalia valor profissional.

## Problemas que a v0.11 resolve

- Análise atual depende demais do DOM visível.
- Prompt atual de GitHub é simples.
- Falta leitura da árvore completa do repo.
- Falta amostragem inteligente de arquivos.
- Falta grafo de dependências.
- Falta evidência por arquivo.
- Falta comparação repo x vaga.
- Falta geração segura de bullets para currículo com suporte em evidência.

## Módulos planejados

```txt
modules/github_analyzer/
  github_client.py
  tree_builder.py
  raw_reader.py
  sampler.py
  dependency_graph.py
  context_builder.py
  schemas.py
  scoring.py
  service.py
```

## Fluxo planejado

```txt
URL do repo
-> owner/repo
-> GitHub API
-> metadata
-> árvore completa
-> arquivos prioritários
-> sampler inteligente
-> leitura raw dos arquivos selecionados
-> grafo de imports
-> contexto estruturado
-> prompt JSON rígido
-> validação Pydantic
-> score técnico + score de portfólio
-> evidence index
-> bullets seguros
-> comparação com vaga/currículo
```

## Arquivos prioritários

O sampler deve priorizar:

- README;
- LICENSE;
- pyproject.toml;
- package.json;
- requirements.txt;
- go.mod;
- Cargo.toml;
- pom.xml;
- build.gradle;
- Dockerfile;
- docker-compose;
- `.github/workflows`;
- arquivos de configuração;
- entrypoints;
- módulos centrais;
- testes;
- docs.

## Ignorar ruído

O sampler deve ignorar:

- `node_modules`;
- `dist`;
- `build`;
- `.venv`;
- `venv`;
- `.pytest_cache`;
- `.ruff_cache`;
- arquivos binários;
- lock files grandes;
- imagens e assets pesados quando não forem relevantes.

## Scores planejados

- technical_quality;
- portfolio_value;
- recruiter_readiness;
- resume_evidence;
- job_alignment;
- documentation;
- tests;
- security;
- architecture;
- maintainability.

## Prompts usados

- `github_repo_analysis_v2`;
- `github_profile_analysis_v1`;
- `portfolio_gap_analysis_v1`.

## Critérios de pronto

- Análise por URL do repo funciona no site/local backend.
- Extensão apenas envia owner/repo e contexto básico.
- Backend faz análise pesada.
- JSON é validado por schema.
- Relatório inclui evidências por arquivo.
- Bullets de currículo têm `supported_by`.
- Sistema não inventa tecnologias ausentes.

---

# v0.12.0 — Match Engine 2.0

## Objetivo

Substituir o matching simples por uma engine multiárea, baseada em requisitos, evidências, domínio profissional, confiança e contexto.

## Problemas que a v0.12 resolve

- Keyword coverage é raso.
- Sinônimos não são suficientes para várias áreas.
- Formação, registro profissional, equipamento e norma precisam de peso próprio.
- Algumas lacunas são críticas e outras são leves.
- Competências transferíveis precisam ser consideradas.
- GitHub e portfólio precisam virar evidência no match.

## Módulos planejados

```txt
modules/matching/
  engine_v2.py
  requirement_matcher.py
  evidence_matcher.py
  score_calculator.py
  explanation_builder.py
  confidence_merger.py
  rules.py
```

## Score sugerido

```txt
Final Match Score =
  25% requisitos obrigatórios
+ 15% requisitos desejáveis
+ 15% formação, credenciais e registros
+ 10% experiência prática
+ 10% domínio profissional
+ 10% evidências de currículo/GitHub/portfólio
+ 5% senioridade
+ 5% preferências e contexto
+ 5% ATS alignment
- penalidades por risco
```

Os pesos podem variar por domínio.

## Regras críticas

### Registros profissionais

Se uma vaga exige registro profissional e o candidato não evidencia o registro, isso deve ser gap crítico.

Exemplo:

```txt
Vaga exige COREN ativo.
Currículo não informa COREN.
Resultado: gap crítico, não recomendável sugerir adicionar sem comprovação.
```

### Obrigatório vs desejável

Faltar requisito obrigatório deve pesar mais que faltar desejável.

### Competências transferíveis

O sistema deve reconhecer transferência de contexto quando houver evidência.

Exemplos:

- professor -> treinamento corporativo;
- psicologia -> RH e recrutamento;
- enfermagem -> healthtech e atendimento clínico;
- engenharia civil -> planejamento, orçamento e gestão;
- design de interiores -> atendimento consultivo e projeto.

### Evidência

O match deve dizer de onde veio cada evidência:

- currículo;
- GitHub;
- portfólio;
- memória local;
- tracker;
- campo revisado pelo usuário.

## Prompts usados

- `match_analysis_evidence_based_v1`;
- `ats_analysis_v1`;
- `resume_tailor_v1`;
- `career_advice_v1`.

## Critérios de pronto

- Match explica requisito por requisito.
- Score final é calculado pelo código.
- IA não decide score final sozinha.
- Gaps críticos aparecem separados.
- Competências transferíveis aparecem com confidence.
- ATS suggestions não inventam informação.
- Testes cobrem múltiplas áreas.

---

# v1.0 — Generalist Career Intelligence Platform

## Objetivo

Fechar uma versão estável, demonstrável e coerente do SotuHire como plataforma local-first de inteligência de carreira.

## Entregáveis esperados

- fluxo currículo + vaga;
- fluxo currículo + vaga + GitHub;
- prompts versionados;
- schemas validados;
- testes multiárea;
- tracker estável;
- docs consistentes;
- exemplos fictícios;
- README limpo;
- demo com áreas diferentes.

## Exemplos mínimos para demo

- Dev backend ou QA;
- Enfermagem ou saúde;
- Engenharia civil ou biomédica;
- Pedagogia ou psicologia;
- Arquitetura/design ou curso técnico.

## Critérios de pronto

- CI passando.
- MkDocs build passando.
- Testes principais passando.
- Nenhum prompt sem schema.
- Nenhuma sugestão que incentive inventar credencial.
- Documentação reflete o estado real.
- Fluxo principal demonstrável em vídeo ou GIF.

---

# Histórico

O histórico detalhado de versões anteriores deve ficar em:

```txt
docs/01-product/roadmap-history.md
```

Este arquivo deve manter o roadmap atual e os próximos marcos. Histórico antigo não deve dominar a primeira leitura do produto.
