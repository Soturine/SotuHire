# Roadmap do SotuHire

Este roadmap descreve o estado atual do SotuHire a partir da v1.0.0 e os próximos refinamentos pós-v1.

O objetivo deste documento é ser uma referência prática para implementação, revisão e criação de prompts para Codex.

## Leitura rápida

| Item | Estado |
|---|---|
| Versão atual considerada | v1.0.0 |
| Natureza da base atual | Produto local-first já funcional, não MVP inicial |
| Próximo ciclo documental | contínuo |
| Próximo ciclo técnico | pós-v1 |
| Foco de produto | Copiloto de carreira multiárea |
| Foco técnico imediato | Refinamento visual, demos guiadas e feedback de uso real |
| Grande lacuna atual | Screenshots/walkthroughs v1 ainda podem ficar mais ricos |
| Risco principal | Adicionar features grandes antes de observar o uso da v1 |

## Estado atual — v1.0.0

A v1.0.0 é a primeira versão estável e demonstrável do produto.

Ela já possui:

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
- Match Engine 2.0 com requisitos, evidências, gaps críticos, confidence e explicação;
- apresentação visual do Match Engine 2.0 no fluxo principal;
- ATS e Resume Tailor usando sinais/evidências do match;
- pesos por domínio profissional;
- demos fictícias multiárea;
- GitHub Pages como site estático de produto/documentação/demo;
- Gemini opcional;
- documentação ampla;
- testes automatizados;
- workflows de qualidade e documentação.

A base até a v1.0.0 prova que o SotuHire existe como produto multiárea demonstrável. A partir daqui, o foco deve ser feedback real, refinamento visual e evolução incremental.

## Diagnóstico atual

### O que está bom

- A visão local-first é forte.
- A separação entre interface, módulos e serviços já existe.
- O projeto já possui testes, CI, documentação e release.
- O produto tem diferenciais bons: memória, tracker, análise de vaga, ATS, extensão e GitHub/portfólio.
- O projeto já tem base suficiente para virar plataforma de inteligência de carreira.

### O que ainda está fraco

- A apresentação v2 já existe, mas pode ganhar screenshots e walkthroughs mais atuais.
- Os parsers ainda carregam viés forte para tecnologia/dev.
- A IA existe, mas ainda não opera por Prompt Registry completo.
- Os prompts atuais implementados no código ainda são pequenos comparados à visão planejada.
- Integrações entre Match Engine 2.0, ATS, Tailor e GitHub Analyzer podem ficar mais visuais.
- A documentação anterior misturava estado atual, histórico antigo e planos futuros.

### O que não deve acontecer agora

- Não adicionar mais features soltas antes de fortalecer a base.
- Não transformar o produto em bot de candidatura automática.
- Não deixar o Gemini decidir score final sem validação do código.
- Não criar regra hardcoded para cada profissão.
- Não tratar GitHub Analyzer como simples leitura de DOM.

## Direção do produto

O SotuHire deve evoluir de:

```txt
ferramenta de análise de currículo/vaga com heurísticas e IA opcional
```

para:

```txt
copiloto local-first de inteligência de carreira, multiárea, explicável e baseado em evidências
```

A evolução deve ser feita por camadas:

1. Extração estruturada de currículo e vaga.
2. Classificação de domínio profissional.
3. Normalização de requisitos e competências.
4. Matching baseado em evidência.
5. ATS e Resume Tailor seguros.
6. GitHub/portfólio como evidência profissional.
7. Tracker e memória como histórico de decisão.

## Linha do tempo planejada

| Versão | Nome | Tipo | Resultado esperado |
|---|---|---|---|
| v0.9.1 | Documentation & Prompt Reorganization | Documentação | Docs coerentes, prompts separados, roadmap atual-first. |
| v0.10.0 | AI Structured Extraction + Domain Intelligence | Código | Currículo e vaga extraídos por IA estruturada com confidence. |
| v0.11.0 | GitHub Analyzer 2.0 | Código | Repositórios analisados por árvore, arquivos, evidências e prompts ricos. |
| v0.12.0 | Match Engine 2.0 | Código | Matching por requisitos, domínio, evidência, risco e confiança. |
| v1.0.0 | Generalist Career Intelligence Platform | Produto | Versão estável, demonstrável e multiárea. |

---

# v0.9.1 — Documentation & Prompt Reorganization

## Objetivo

Transformar a documentação em uma base clara para implementação com Codex.

Esta versão não implementa feature nova no código. Ela organiza decisão de produto, roadmap, arquitetura de prompts e contratos de IA.

## Entregas obrigatórias

### Produto

- Reescrever `docs/01-product/vision.md` sem duplicação histórica.
- Reescrever `docs/01-product/roadmap.md` como roadmap atual-first.
- Criar `docs/01-product/roadmap-history.md` para histórico de versões anteriores.
- Manter `docs/01-product/multi-domain-product-strategy.md` como estratégia complementar.

### IA

- Criar `docs/04-ai/prompt-architecture.md`.
- Criar `docs/04-ai/prompt-registry.md`.
- Transformar `docs/04-ai/prompt-catalog.md` em índice.
- Criar `docs/04-ai/prompts/README.md`.
- Separar cada prompt em arquivo próprio.

### Prompts documentados

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

## Fora de escopo da v0.9.1

- Implementar código novo.
- Refatorar módulos existentes.
- Alterar extensão.
- Alterar regras de fontes de dados.
- Criar provider novo de IA.
- Mudar persistência local.

## Critérios de pronto

- Roadmap começa pelo estado atual real da v0.9.0.
- Vision não tem seções duplicadas ou remendadas.
- Histórico antigo fica separado em `roadmap-history.md`.
- Cada prompt tem arquivo próprio.
- Cada prompt informa entrada, saída, regras, confidence, exemplos e critérios de validação.
- `mkdocs.yml` possui navegação para os novos documentos.
- `CHANGELOG.md` registra a reorganização.

---

# v0.10.0 — AI Structured Extraction + Domain Intelligence

## Objetivo

Fazer o SotuHire extrair currículo e vaga com IA estruturada, sem depender apenas das heurísticas atuais.

A v0.10.0 deve ser o primeiro ciclo técnico depois da reorganização documental.

## Problema que resolve

Hoje, parsers e listas de skills ainda tendem a funcionar melhor para TI/dev. Isso limita a visão multiárea.

A v0.10.0 deve permitir que o SotuHire entenda currículos e vagas de áreas como:

- tecnologia;
- cybersecurity;
- engenharia biomédica;
- engenharia civil;
- arquitetura;
- design de interiores;
- enfermagem;
- psicologia;
- pedagogia;
- administração;
- financeiro;
- marketing;
- logística;
- cursos técnicos;
- saúde;
- educação;
- humanas;
- exatas;
- indústria.

## Módulos planejados

```txt
modules/ai/
  prompt_registry.py
  json_guard.py
  orchestration.py
  prompts/
  schemas/
    resume_extraction.py
    job_extraction.py
    domain_classification.py

modules/domain_intelligence/
  classifier.py
  requirement_classifier.py
  catalog_loader.py
  taxonomy.py
  transferable_skills.py
  confidence_merger.py
```

## Funcionalidades

### Extração de currículo por IA

Entrada:

- texto bruto do currículo;
- tipo do arquivo;
- preferências do usuário;
- memória profissional opcional;
- contexto de área alvo, se existir.

Saída:

- identidade;
- formação;
- experiências;
- projetos;
- skills;
- ferramentas;
- idiomas;
- certificações;
- registros profissionais;
- domínios profissionais;
- senioridade estimada;
- seções ausentes;
- confidence por campo.

### Extração de vaga por IA

Entrada:

- texto bruto da vaga;
- URL ou fonte, se disponível;
- contexto de origem;
- preferências do usuário.

Saída:

- título;
- empresa;
- domínio;
- senioridade;
- localidade;
- modelo de trabalho;
- tipo de contrato;
- requisitos obrigatórios;
- requisitos desejáveis;
- responsabilidades;
- benefícios;
- red flags;
- requisitos com categoria e criticalidade.

### Domain Intelligence

O sistema deve classificar requisitos em categorias como:

- formação;
- experiência;
- hard skill;
- soft skill;
- ferramenta;
- software;
- equipamento;
- metodologia;
- norma;
- certificação;
- registro profissional;
- idioma;
- portfólio;
- disponibilidade;
- localização;
- ambiente de atuação.

## Regras importantes

- A IA extrai e classifica.
- O código valida e calcula.
- Campos com confidence baixa devem ir para revisão.
- Parser heurístico continua existindo como fallback.
- O sistema não deve inventar formação, experiência, certificação ou registro.

## Prompts usados

- `resume_extraction_v1`;
- `job_extraction_multi_domain_v1`;
- `domain_classification_v1`.

## Testes obrigatórios

Fixtures mínimas:

- currículo de dev + vaga backend;
- currículo de enfermagem + vaga hospitalar;
- currículo de pedagogia + vaga escola;
- currículo de engenharia civil + vaga de obras;
- currículo de psicologia + vaga RH/clínica;
- currículo técnico + vaga manutenção;
- vaga curta informal;
- vaga longa corporativa;
- currículo com informação faltante;
- currículo com registro profissional ausente.

## Critérios de pronto

- Saída validada por Pydantic.
- Prompt versionado.
- Retry para JSON inválido.
- Confidence por campo.
- Fallback heurístico.
- UI mostra campos incertos.
- Testes cobrem pelo menos cinco áreas diferentes.

---

# v0.11.0 — GitHub Analyzer 2.0

## Objetivo

Evoluir a análise de GitHub/portfólio para um nível mais profundo, inspirado por pipelines de análise de repositório que usam árvore completa, arquivos selecionados, prompt estruturado e scoring por dimensão.

## Problema que resolve

A análise atual do SotuHire identifica sinais úteis, mas ainda é rasa para avaliar um repositório como evidência profissional.

Ela precisa sair de:

```txt
sinais visíveis + heurísticas simples + refinamento textual
```

para:

```txt
repo metadata + árvore completa + arquivos relevantes + evidências + prompt JSON + score técnico e profissional
```

## Módulos planejados

```txt
modules/github_analyzer/
  github_client.py
  tree_builder.py
  raw_file_reader.py
  sampler.py
  dependency_graph.py
  context_builder.py
  evidence_index.py
  scoring.py
  schemas.py
  service.py
```

## Fluxo planejado

1. Receber URL, owner/repo ou payload da extensão.
2. Buscar metadados públicos do repositório.
3. Buscar árvore completa do branch principal.
4. Construir árvore textual filtrada.
5. Selecionar arquivos prioritários.
6. Ler conteúdo raw dos arquivos selecionados.
7. Detectar manifestos, workflows, testes, docs e configs.
8. Construir grafo simples de dependências por imports.
9. Montar contexto para IA.
10. Chamar prompt `github_repo_analysis_v2`.
11. Validar JSON.
12. Calcular scores finais no código.
13. Gerar evidências por arquivo.
14. Salvar resultado no perfil/portfólio/memória quando o usuário escolher.

## Dimensões de análise

- testes;
- segurança;
- arquitetura;
- qualidade de código;
- documentação;
- consistência;
- manutenibilidade;
- valor de portfólio;
- evidência para currículo;
- prontidão para recrutador;
- aderência a vaga alvo, se houver.

## Saídas esperadas

- score técnico;
- score de portfólio;
- score de evidência curricular;
- grade;
- resumo profissional;
- stack detectada;
- skills demonstradas;
- evidências por arquivo;
- pontos fortes;
- pontos fracos;
- inconsistências;
- flags de segurança;
- recomendações priorizadas;
- bullets seguros para currículo;
- tipos de vaga onde o repo ajuda.

## Prompts usados

- `github_repo_analysis_v2`;
- `github_profile_analysis_v1`;
- `portfolio_gap_analysis_v1`.

## Critérios de pronto

- Não depender apenas do DOM da página.
- Analisar árvore completa conhecida.
- Não afirmar ausência de teste se teste aparece na árvore.
- Não inventar deploy, usuários, métricas ou empresas.
- Gerar evidência por arquivo.
- Separar score técnico de score de portfólio.
- Ter fallback local quando IA não estiver disponível.

---

# v0.12.0 — Match Engine 2.0

## Objetivo

Substituir o matching baseado principalmente em palavras por uma engine multiárea baseada em requisitos, evidências, domínio, risco e confiança.

## Problema que resolve

A mesma lógica de matching não serve para todas as áreas quando ela só compara keywords.

Exemplos:

- Enfermagem pode depender de registro, setor e procedimentos.
- Psicologia pode depender de abordagem, CRP, público atendido e contexto de atuação.
- Engenharia civil pode depender de obra, orçamento, AutoCAD, Revit, normas e acompanhamento.
- Pedagogia pode depender de BNCC, alfabetização, inclusão e etapa escolar.
- Cybersecurity pode depender de SIEM, SOC, resposta a incidentes, hardening e frameworks.
- Arquitetura/interiores pode depender de portfólio, software, projeto executivo e atendimento.

## Módulos implementados

```txt
modules/matching/
  __init__.py
  models.py
  exceptions.py
  engine.py
  requirement_matcher.py
  evidence_matcher.py
  transferable_skills.py
  score_calculator.py
  risk_adjustment.py
  confidence.py
  explanation_builder.py
```

## Fórmula implementada

| Categoria | Peso |
|---|---:|
| Requisitos obrigatórios | 30% |
| Requisitos desejáveis | 15% |
| Aderência de domínio | 10% |
| Senioridade | 10% |
| Formação, certificações e registros | 10% |
| Força das evidências | 10% |
| Evidências GitHub/portfolio | 5% |
| ATS keyword alignment | 5% |
| Preferências e logística | 5% |

O `risk_adjustment` aplica penalidade depois do cálculo base.

## Regras de matching

- Requisito obrigatório ausente pesa mais que desejável ausente.
- Requisito eliminatório ausente deve gerar gap crítico.
- Registro profissional obrigatório não pode ser inferido sem evidência.
- Competência transferível pode reduzir gap, mas não deve virar match completo sem evidência.
- Evidence score deve diferenciar currículo, GitHub, portfólio e memória.
- A IA pode sugerir match status, mas o score final deve ser calculado pelo código.

## Prompts usados

- `match_analysis_evidence_based_v1`;
- `ats_analysis_v1`;
- `resume_tailor_v1`;
- `career_advice_v1`.

## Critérios de pronto

- Explicação para score e requisitos principais.
- Suporte a required/preferred/optional/knockout.
- Multiárea testado com fixtures.
- Gaps críticos destacados e score travado quando necessário.
- Sugestões seguras, sem inventar experiência ou registro profissional.
- Engine antiga preservada como fallback.

---

# v1.0.0 — Generalist Career Intelligence Platform

## Objetivo

Fechar uma versão estável, demonstrável e confiável do SotuHire como plataforma local-first de inteligência de carreira.

## O que precisa estar pronto

- Roadmap e docs coerentes.
- Currículo e vaga extraídos com IA estruturada e fallback.
- Domain Intelligence funcionando para múltiplas áreas.
- Match Engine 2.0 com explicação.
- ATS e Resume Tailor seguros.
- GitHub Analyzer 2.0 conectado a evidências profissionais.
- Tracker útil para acompanhamento real.
- Exemplos multiárea.
- Testes de regressão.
- CI e docs passando.
- README com demo clara.

## Demonstrações recomendadas

A v1.0 inclui cenários fictícios para demonstração:

1. Dev/Backend ou Cybersecurity.
2. Enfermagem ou saúde.
3. Engenharia civil ou biomédica.
4. Pedagogia, psicologia, arquitetura ou curso técnico.

Cada demo deve mostrar:

- currículo;
- vaga;
- extração estruturada;
- matching;
- ATS;
- sugestões;
- evidências;
- plano de melhoria.

## Fora de escopo permanente

- Prometer contratação.
- Inventar credenciais.
- Substituir decisão humana.
- Fazer score sem explicação.
- Tratar todas as profissões como se fossem tecnologia.

## Sequência recomendada de commits depois da documentação

```txt
1. docs: reorganize roadmap vision and AI prompts
2. feat(ai): add prompt registry and JSON guard
3. feat(ai): add structured resume extraction schemas
4. feat(ai): add multi-domain job extraction schemas
5. feat(domain): add domain intelligence classifier
6. feat(match): add evidence-based matching engine
7. feat(github): add GitHub Analyzer 2.0 pipeline
```
