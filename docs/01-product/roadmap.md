# Roadmap do SotuHire

Este roadmap descreve o estado atual do SotuHire a partir da v1.9.2 e os próximos ciclos técnicos.

O objetivo deste documento é ser uma referência prática para implementação, revisão e criação de prompts para Codex.

## Leitura rápida

| Item | Estado |
|---|---|
| Versão atual considerada | v1.9.2 |
| Natureza da base atual | Produto local-first web-first funcional, com API, frontend, IA opcional e intake persistente |
| Próximo ciclo documental | contínuo |
| Próximo ciclo técnico | v1.9.3 Public Exams / Edital Parser Foundation ou v2.0 Assistant workflows with human approval |
| Foco de produto | Copiloto de carreira multiárea com Perfil central, Radar local-first e trajetórias acadêmicas |
| Foco técnico imediato | Evidências acadêmicas, RAG local aplicado e documentação profissional |
| Grande lacuna atual | Upload direto de PDF/HTML do Lattes, parser real de edital/concurso e matching adaptativo por domínio |
| Risco principal | Persistir segredos ou mover regra crítica para o frontend visual |

## Estado atual - v1.9.2

A v1.9.2 entrega **Lattes, Perfil Acadêmico e Extração de Evidências Assistida por IA**:

- cria `modules/academic` com parser local para texto colado do Currículo Lattes;
- adiciona endpoints `/api/v1/profile/import-lattes`, `/api/v1/profile/lattes/draft` e `/api/v1/profile/lattes/confirm`;
- registra o prompt `profile_lattes_extractor_v1` para Gemini opcional;
- adiciona seção **Acadêmico / Lattes** em `/profile`;
- gera candidatos revisáveis de `ProfileItem` para formação, pesquisa, publicações, extensão, docência, monitoria, eventos, prêmios, bolsas e produção técnica/artística;
- confirma itens acadêmicos somente após seleção explícita da pessoa usuária;
- integra evidências acadêmicas ao Career Context Engine com purposes `academic`, `lattes` e `public_exams`;
- reforça ATS, Tailor, Match e GitHub/Portfólio para usar evidências acadêmicas sem tratá-las automaticamente como experiência corporativa;
- documenta a fundação futura para editais e concursos, sem implementar inscrição automática nem Concurso Mode completo;
- revisa README e docs principais em PT-BR com acentos e linguagem mais consistente.

## Estado atual - v1.9.1

A v1.9.1 entrega **Integridade de Release, README profissional e Career Context Engine**:

- revisa a integridade da tag `v1.9.0` para o estado final com lockfile validado;
- confirma `npm ci` e validações do frontend antes da nova release;
- reestrutura o README como página de produto/repo;
- atualiza screenshots e GIF do frontend web moderno com nomes sem versão;
- cria `modules/context` como Career Context Engine;
- unifica Perfil Profissional Universal, RAG local e sinais do produto em contexto serializável;
- integra contexto em Wishlist, Radar, Scheduler, Match, ATS, Tailor, Tracker, Fontes, Notificações e GitHub/Portfólio;
- adiciona candidatos de evidência de GitHub/Portfólio para revisão, sem salvar automaticamente no Perfil;
- preserva o fluxo authenticated browser existente.

## Estado atual - v1.9.0

A v1.9.0 entrega **Radar Agendado e Notificações Locais**:

- cria agendamentos locais do Radar por wishlist, fonte, palavras-chave e preferências;
- adiciona store local para schedules, runs agendadas e notificações;
- adiciona quiet hours, cooldown contra alertas repetidos e histórico de execuções;
- expõe endpoints `/api/v1/radar/schedules`, `/api/v1/radar/scheduled-runs`,
  `/api/v1/radar/scheduler/*` e `/api/v1/notifications`;
- adiciona UI de Agendamentos e Central de Notificações dentro do Radar;
- usa o Perfil Profissional Universal quando `use_profile_context=true`;
- mantém execução revisável: resultados podem ir para Caixa de Entrada ou Tracker apenas por ação
  manual da pessoa usuária;
- permite fontes de captura assistida autenticada como lembrete agendável, sem coletar cookies,
  tokens, sessão, headers ou storage de terceiros.

O scheduler roda somente enquanto a API local está ativa. Ele não é daemon de sistema operacional,
não faz auto-apply e não substitui revisão humana.

## Estado atual - v1.8.2

A v1.8.2 entrega o **Perfil Profissional Universal**:

- cria `modules/profile` com modelos, store local, serviço, extração local e deduplicação;
- adiciona API `/api/v1/profile` para CRUD do perfil, importação de texto, dedupe e contexto;
- adiciona tela `/profile` no frontend moderno;
- permite editar dados básicos, adicionar item manual, filtrar por tipo, editar evidências e
  remover itens;
- importa texto de currículo, Lattes, portfólio, certificados e notas como rascunho revisável;
- registra o prompt `profile_items_extractor_v1` para IA opcional;
- mantém fallback local multiárea quando IA está desligada ou falha;
- conecta o perfil persistido ao draft da Wishlist quando `use_profile_context=true`;
- adiciona integração inicial segura de perfil em Match/Tailor e fontes/captura;
- adiciona `POST /api/v1/sources/authenticated-captures` para captura assistida autenticada com
  revisão humana, sem cookie, token, sessão, headers, CAPTCHA bypass ou auto-apply.

O SotuHire continua sem assumir TI/dev, GitHub, CLT, graduação, experiência formal ou registro
profissional. Registros profissionais só são tratados como fato quando aparecem em evidência.

## Estado atual - v1.8.1

A v1.8.1 consolida o **Radar de Vagas**:

- adiciona `POST /api/v1/radar/wishlists/draft` para transformar texto livre em rascunho de
  wishlist;
- registra `job_wishlist_builder_v1` para IA opcional;
- mantém fallback local multiárea, sem assumir TI, GitHub, CLT, diploma ou experiência formal;
- prepara `ProfileContext` e `ProfileContextOrchestrator` como base para Perfil Profissional
  Universal;
- amplia toggles seguros de IA para currículo, vaga, match, ATS, tailor, GitHub, importações e
  Radar;
- melhora `/radar` com criação assistida de wishlist, erros de fonte visíveis e execução desabilitada
  quando não há fonte ativa;
- inclui frontend e empacotamento da extensão no CI.

Nenhuma wishlist é salva automaticamente; a pessoa revisa e edita antes de salvar.

## Estado atual - v1.8.0

A v1.8.0 adiciona o **Radar de Vagas**:

- tela `/radar` com Resumo, Wishlist, Fontes, Rodadas, Resultados e Alertas;
- wishlists locais com cargos, skills, locais, modelo de trabalho e score mínimo;
- RSS/Atom público com refresh manual;
- estrutura de adapters para APIs oficiais documentadas;
- resultados do Radar com score local, evidências, lacunas e próximas ações;
- alertas locais para vagas acima do score mínimo;
- ações para salvar na Caixa de Entrada ou em Candidaturas;
- IA opcional apenas para explicação via `job_radar_match_explanation_v1`, sem decidir score final;
- Streamlit continua legado/dev e não foi removido.

## Estado atual - v1.7.1

A v1.7.1 consolida o frontend web-first e melhora **Fontes e Captura** como fluxo de intake:

- v1.7.0 implementou importadores de texto, link, CSV e JSON, Caixa de Entrada, histórico,
  deduplicação e integração com Candidaturas/Kanban;
- v1.7.1 adiciona upload real de CSV/JSON pelo navegador, preview antes de importar, mescla visual
  de duplicatas, exportação CSV/JSON, Diretório de Fontes e teste anti-mojibake;
- IA em importações é parcial/opcional: usa `source_import_enrichment_v1` quando provider está
  configurado e cai para local se falhar;
- RSS/feed recorrente era roadmap; na v1.8.0 virou Radar manual com RSS/Atom público;
- Streamlit continua legado/dev e não foi removido.

## Estado atual — v1.3.0

A v1.3.0 mantém a base estável da v1.2.0 e adiciona o frontend moderno em `apps/web`.

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
- Análise de Compatibilidade com requisitos, evidências, gaps críticos, confiança e explicação;
- apresentação visual da Análise de Compatibilidade no frontend moderno;
- ATS e Resume Tailor usando sinais/evidências do match;
- pesos por domínio profissional;
- demos fictícias multiárea;
- GitHub Pages como site estático de produto/documentação/demo;
- home profissional em `docs/index.md`;
- documentação frontend-ready em `docs/08-frontend`;
- contratos de API real para Lovable/React;
- FastAPI local em `apps/api`, com OpenAPI e endpoints `/api/v1`;
- mocks JSON oficiais em `docs/assets/mock-api`;
- demo estática v1.1 com contrato conectável a backend local;
- frontend moderno em `apps/web`, com modo Demo e modo API Real;
- tela Fontes e Captura integrada ao menu e à rota `/sources`;
- UI planejada de IA e Providers sem persistir segredos no frontend;
- Gemini opcional;
- documentação ampla;
- testes automatizados;
- workflows de qualidade e documentação.

A base até a v1.3.0 prova que o SotuHire existe como produto multiárea demonstrável, com API
versionada local e frontend moderno. A partir daqui, o foco técnico deve ser consolidar settings
seguros, manter Streamlit como modo local/dev e preservar o core como fonte de verdade.

## Diagnóstico atual

### O que está bom

- A visão local-first é forte.
- A separação entre interface, módulos e serviços já existe.
- O projeto já possui testes, CI, documentação e release.
- O produto tem diferenciais bons: memória, tracker, análise de vaga, ATS, extensão e GitHub/portfólio.
- O projeto já tem base suficiente para virar plataforma de inteligência de carreira.

### O que ainda está fraco

- A apresentação web moderna já existe e tem screenshots e walkthroughs atuais.
- Os parsers ainda precisam melhorar cobertura por domínio, apesar do avanço em Lattes/acadêmico.
- O Prompt Registry existe, mas precisa de governança e cobertura contínua.
- Os prompts atuais implementados no código ainda podem ganhar exemplos e critérios por domínio.
- Settings/IA existem, mas precisam de auditoria contínua de UX e segurança.
- A lacuna atual é aprofundar matching adaptativo por domínio, upload direto para Perfil e revisão avançada de evidências GitHub/Portfólio.
- Upload direto de PDF/HTML do Lattes, parser real de edital/concurso e plano de estudo por edital seguem como evoluções futuras.
- A documentação anterior misturava estado atual, histórico antigo e planos futuros.

### O que não deve acontecer agora

- Não adicionar mais features soltas antes de fortalecer a base.
- Não transformar o produto em bot de candidatura automática.
- Não deixar o Gemini decidir score final sem validação do código.
- Não criar regra hardcoded para cada profissão.
- Não tratar GitHub Analyzer como simples leitura de DOM.
- Não reimplementar matching, ATS, Tailor ou regras anti-invenção no frontend.

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
| v1.1.0 | Professional Frontend Handoff and Product Site | Produto/docs | Site profissional, handoff Lovable, contratos e mocks. |
| v1.2.0 | API Layer / FastAPI Foundation | Código | API HTTP versionada para consumir o core local-first. |
| v1.3.0 | Modern Web Frontend | Frontend | Frontend moderno com modo Demo e API Real. |
| v1.4.0 | Streamlit Legacy Mode | Produto | Streamlit mantido como modo local/dev legado. |
| v1.7.0 | Public Sources, Importers & Capture History | Produto | Importadores, Caixa de Entrada, histórico e dedupe local. |
| v1.7.1 | Intake Polish, Encoding Fixes & Source Discovery Prep | Produto | Upload real, merge visual, exportação e Diretório de Fontes. |
| v1.8.0 | Job Radar, Public Feeds & Wishlist Alerts | Produto | Radar manual, RSS público, wishlist e alertas locais. |
| v1.8.1 | AI Wishlist, Radar Stability & Profile Context Prep | Produto | Wishlist por IA/local, contexto profissional preparado e CI web. |
| v1.8.2 | Universal Professional Profile | Produto/core | Perfil Profissional Universal editável, multiárea e evidence-first. |
| v1.9.0 | Scheduled Radar & Notifications | Produto | Agendamento local do Radar, quiet hours, cooldown e notificações in-app. |
| v1.9.1 | Release Integrity, README Overhaul & Context Unification | Produto/core/docs | Integridade de tag, README profissional, screenshots web e Career Context Engine. |
| v1.9.2 | Lattes, Academic Profile & AI-Assisted Evidence Extraction | Produto/core/docs | Importação Lattes por texto, evidências acadêmicas revisáveis, Gemini opcional e fundação de editais. |
| v1.9.3 | Public Exams / Edital Parser Foundation | Produto/core/docs | Parser inicial de edital, requisitos e cronogramas, sem inscrição automática. |
| v2.0.0 | Assistant autônomo com aprovação manual | Produto/arquitetura | Autonomia local com aprovações explícitas e sem auto-apply. |

---

# v1.3.0 — Modern Web Frontend / Lovable Integration

## Objetivo

Integrar o frontend moderno em `apps/web`, mantendo backend, Streamlit, docs e testes existentes.

## Entregas

- Criar app React/Vite em `apps/web`.
- Implementar Home, Dashboard, Currículo, Vaga, Análise de Compatibilidade, ATS, Ajuste, GitHub,
  Candidaturas, Inteligência, Fontes e Captura, Configurações e Privacidade.
- Manter Modo Demo com dados fictícios.
- Conectar Modo API Real a `http://127.0.0.1:8787/api/v1`.
- Tratar envelope `{ ok, data, warnings, request_id }`.
- Manter rodapé discreto com versão e API local.
- Documentar IA e Providers como planejado para endpoints seguros futuros.
- Gerar screenshots e GIF do frontend moderno.

## Fora de escopo

- Remover Streamlit.
- Reimplementar score real no frontend.
- Salvar API key no browser.
- Implementar scraper autenticado, crawler logado, auto apply ou automação de plataformas.

## Próximos ciclos

- v1.4.0: Streamlit Legacy Mode e endpoints seguros de Settings/IA.
- v2.0.0: SaaS-ready Architecture.

---

# v1.2.0 — API Layer / FastAPI Foundation

## Objetivo

Criar uma API HTTP local e versionada para que um frontend moderno consuma o core Python sem
reimplementar regra de negócio no browser.

## Entregas

- Criar `apps/api` com FastAPI, routers, DTOs Pydantic e services finos.
- Expor OpenAPI em `/openapi.json` e docs interativas em `/docs`.
- Implementar endpoints `/api/v1` para health, resume/job extraction, match, ATS, Tailor, GitHub
  Analyzer, tracker e Application Intelligence.
- Adicionar CORS restrito por default e configuração por env.
- Criar `scripts/run_api.py`.
- Manter Streamlit e Local Companion API funcionando.
- Atualizar contratos, arquitetura, handoff Lovable, README e changelog.

## Fora de escopo

- Criar frontend moderno completo.
- Publicar API em ambiente SaaS.
- Remover Streamlit.
- Substituir Local Companion API.

## Próximos ciclos

- v1.4.0: Streamlit Legacy Mode.
- v2.0.0: SaaS-ready Architecture.

---

# v1.1.0 — Professional Frontend Handoff and Product Site

## Objetivo

Preparar o SotuHire para um frontend profissional futuro sem remover Streamlit e sem mover regra
crítica para o browser.

## Entregas

- Criar `docs/08-frontend` com arquitetura, handoff Lovable, screen map, API contract, mocks,
  design notes, frontend rules e Application Intelligence.
- Criar mocks oficiais em `docs/assets/mock-api`.
- Criar home dedicada `docs/index.md`.
- Transformar `docs/README.md` em índice documental do repositório.
- Criar demo estática v1.1 para site e Lovable.
- Reservar `apps/web` para futuro frontend moderno.

## Fora de escopo

- Implementar API FastAPI completa.
- Criar app React/Next completo.
- Remover Streamlit.
- Alterar coleta autenticada.
- Colocar chaves ou tokens no frontend.

## Próximos ciclos

- v1.3.0: Modern Web Frontend.
- v1.4.0: Streamlit Legacy Mode.
- v2.0.0: SaaS-ready Architecture.

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
