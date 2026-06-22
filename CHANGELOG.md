# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

## Unreleased

## [1.1.0] - 2026-06-22

### Adicionado

- Documentação frontend-ready em `docs/08-frontend`, incluindo arquitetura, handoff Lovable,
  screen map, API contract, mock data contract, design notes, frontend rules e Application
  Intelligence.
- Mocks JSON oficiais em `docs/assets/mock-api` para prototipação de frontend.
- Home pública dedicada em `docs/index.md` para o GitHub Pages.
- Demo estática v1.1 em `docs/08-frontend/static-demo.md`.
- Estrutura reservada `apps/web` para um frontend moderno futuro.

### Alterado

- `docs/README.md` passou a ser índice documental do repositório, enquanto `docs/index.md` virou a
  home do site.
- Roadmap atualizado com v1.1.0, v1.2.0, v1.3.0, v1.4.0 e v2.0.0.
- README raiz passou a explicar Streamlit como app local atual/dev, GitHub Pages como site estático
  e Lovable/React como frontend futuro guiado por contratos.

### Segurança

- Documentado que o frontend futuro não deve conter API keys, Gemini key, GitHub token ou regras
  críticas de negócio.
- Reforçado que GitHub Pages continua estático e não roda backend.
- Mocks usam apenas dados fictícios.

### Validação

- QA final planejado com `ruff check .`, `ruff format --check .`, `pytest`, `mkdocs build --strict`,
  `python -m compileall modules tests`, `pyright` e `node --check docs/javascripts/sotuhire-demo.js`.

## [1.0.0] - 2026-06-21

### Adicionado

- Apresentação do Match Engine 2.0 no fluxo principal, com `Confidence`, `Evidence Score`, gaps
  críticos, requisitos atendidos/parciais/ausentes, competências transferíveis, evidências usadas e
  ações seguras.
- Enriquecimento determinístico do `analyze_structured` com Match Engine 2.0, mantendo fallback
  legado quando a extração estruturada local não estiver disponível.
- Classificação ATS baseada em evidências do Match Engine 2.0, separando keywords presentes,
  keywords que só devem ser adicionadas se forem verdadeiras e keywords sem evidência.
- Resume Tailor usando evidências do Match Engine 2.0 para keywords seguras, warnings e gaps
  críticos.
- Pesos configuráveis por domínio em `modules/matching/domain_weights.py`, com perfis iniciais para
  enfermagem/saúde, arquitetura, cybersecurity, pedagogia e engenharia civil.
- Demos fictícias multiárea em `examples/` e outputs estáticos em `examples/outputs/`.
- GitHub Pages preparado como site estático de produto, documentação e demo, com páginas sobre
  demo v1.0 e diferença entre Pages e app local.
- Documento de desenvolvimento `docs/07-development/v1.0.0-stable-release.md`.

### Alterado

- Versão do projeto atualizada para `1.0.0`.
- README, roadmap, visão, regras de matching e docs do Match Engine foram atualizados para refletir
  a versão estável v1.0.0.
- A home do MkDocs passou a apresentar o produto como site público estático, sem prometer execução
  do backend no GitHub Pages.
- A UI diferencia melhor score, confidence, evidência e risco.

### Segurança

- O GitHub Pages é documentado explicitamente como site estático; o app completo continua local via
  Streamlit/Local Companion API.
- Demos usam apenas nomes, empresas e cenários fictícios.
- Tailor e ATS preservam linguagem condicional para itens sem evidência.
- Nenhum comportamento de coleta autenticada, compliance ou exposição de API keys foi alterado.

### Validação

- QA final executado com `ruff check .`, `ruff format --check .`, `pytest`, `mkdocs build --strict`,
  `python -m compileall modules tests` e `pyright`.

## [0.12.0] - 2026-06-21

### Adicionado

- Módulo `modules/matching` com models Pydantic, exceptions, requirement matcher, evidence matcher,
  transferable skills, score calculator, risk adjustment, confidence scoring, explanation builder e
  engine determinística.
- Catálogo inicial de registros e conselhos profissionais brasileiros no Domain Intelligence e no
  Requirement Matcher, incluindo CRM, CRO, CRF, COREN, CREFITO, CRN, CRMV, CRP, CREF, CRTR, CREA,
  CAU, CFT, CRT, CRQ, OAB, CRC, CRA, CORECON, CRB, CRESS, CONRERP, CRECI, CRBio e MTE/DRT.
- Classificação de MTE/DRT como `professional_registration`, separada de `professional_license`.
- `ProfessionalRegistrationInput` e opção genérica `Outro conselho / Outro registro profissional`
  para cadastro/manual review de registros profissionais.
- Integração incremental `analyze_job_v2` no analyzer atual, mantendo `analyze_job` como fallback
  legado.
- Fixtures multiárea para backend, enfermagem, pedagogia, psicologia, engenharia civil,
  arquitetura, cybersecurity e evidências GitHub/portfolio.
- Testes dedicados para requirement matching, evidence matching, transferable skills, scoring,
  explanation builder, confidence, risk adjustment e engine v2.

### Alterado

- Match Engine 2.0 passa a calcular score por código com pesos para requisitos obrigatórios,
  desejáveis, domínio, senioridade, formação/credenciais, evidências, GitHub/portfolio, ATS,
  preferências e penalidade de risco.
- Registros profissionais obrigatórios ausentes passam a gerar gap crítico e limitam o score,
  sem serem compensados por soft skills ou competências transferíveis.
- Evidências do GitHub Analyzer 2.0 podem contribuir para evidence score e explicação quando
  disponíveis.
- Aliases de domínio passam a inferir categorias quando o requisito chega sem categoria explícita.
- Importação pública de `modules/matching` ficou lazy para evitar ciclos de importação.
- Versão do projeto atualizada para `0.12.0`.

### Segurança

- Sugestões para registros profissionais usam linguagem condicional, como "se possuir" e "se houver
  evidência", sem recomendar invenção de credenciais.
- A engine diferencia match direto de competência transferível e não transforma projeto pessoal em
  experiência corporativa.
- Nenhum comportamento de coleta autenticada, compliance ou exposição de API keys foi alterado.

### Documentação

- Regras de matching, regras multiárea, roadmap, README e docs de desenvolvimento atualizados para
  refletir o Match Engine 2.0 implementado.
- Prompts `match_analysis_evidence_based_v1`, `ats_analysis_v1`, `resume_tailor_v1` e
  `career_advice_v1` revisados para contratos, confidence, anti-fabrication e integração com
  evidências/Match Engine 2.0.

## [0.11.0] - 2026-06-21

### Adicionado

- Módulo `modules/github_analyzer` com cliente GitHub público, modelos Pydantic, tree builder,
  filtros, sampler, dependency graph, context builder, evidence index, schemas, scoring e service.
- Suporte a `GITHUB_TOKEN` opcional no cliente GitHub para aumentar rate limit sem exigir token em
  repositórios públicos simples.
- Registro do prompt `github_repo_analysis_v2` no Prompt Registry, com saída validável por JSON
  Guard/Pydantic.
- Pipeline determinístico de fallback para gerar relatório parcial quando a GitHub API falha ou
  quando só há sinais capturados pela extensão.
- Fixtures e testes unitários para URL parsing, árvore, sampler, dependency graph, context builder,
  evidence index, scoring, service e fallback.

### Alterado

- Local Companion API passa a usar o GitHub Analyzer 2 quando o payload da extensão solicita análise
  por API, mantendo o analyzer antigo de portfólio como fallback.
- A extensão continua leve e apenas sinaliza `analysis_result.use_github_api` para o backend local.
- Arquivos `requirements*.txt` foram movidos para `docs/requirements/`, mantendo a raiz mais limpa.
- Versão do projeto atualizada para `0.11.0`.

### Segurança

- Tokens GitHub são opcionais, lidos por ambiente e não são enviados para a extensão/frontend.
- O scoring aplica trava de segurança quando evidências indicam possível segredo exposto.
- A análise diferencia arquivo presente na árvore de conteúdo realmente lido.
- Nenhum comportamento de coleta autenticada foi alterado.

### Documentação

- Prompt playbook `github_repo_analysis_v2` revisado para refletir o pipeline implementado.
- Docs de GitHub/portfólio e roadmap atualizados para a v0.11.0.

## [0.10.0] - 2026-06-21

### Adicionado

- Base de Prompt Registry com `PromptSpec` versionado, carregamento lazy de prompts e prompts
  iniciais para resume extraction, multi-domain job extraction e domain classification.
- JSON Guard para respostas de IA, incluindo limpeza de Markdown fences, parse de JSON, validação
  Pydantic e detecção de campos com baixa confiança.
- Schemas Pydantic para `ResumeExtractionOutput`, `JobExtractionOutput` e
  `DomainClassificationOutput`, com confidence limitado a `0..1`.
- Base de Domain Intelligence com catálogo multiárea, aliases e classificação determinística para
  software, cybersecurity, engineering, nursing, psychology, pedagogy, architecture, healthcare,
  education, perfis técnicos e perfis generalistas.
- Serviços estruturados de resume, job e domain classification, com execução provider-aware e
  fallback heurístico local.
- Suporte no provider Gemini para extração estruturada por prompt específico sem expor API keys.
- Fixtures fictícias multiárea para currículos e vagas em technology, healthcare, education,
  engineering, architecture, cybersecurity e technical maintenance.

### Alterado

- Versão do projeto atualizada para `0.10.0`.
- `modules/ai` passa a exportar serviços de structured extraction além do fluxo de análise
  existente.
- Parsers existentes permanecem como fallback local e não são substituídos por saída de IA.

### Testes

- Cobertura adicionada para Prompt Registry, JSON Guard, schema de resume extraction, schema de job
  extraction, Domain Intelligence e comportamento de fallback da structured extraction.
- Testes com fake provider garantem que a structured extraction nunca chama uma API real na suíte.

### Segurança

- Saídas de IA continuam consultivas e precisam passar por validação Pydantic antes de entrar em
  fluxos do produto.
- Registros profissionais como COREN, CRP, CREA e CAU são detectados como sinais regulados, não
  inventados.
- Nenhum comportamento de coleta autenticada foi alterado.

## [0.9.1] - 2026-06-21

### Documentation

- alinhado `docs/01-product/roadmap.md` ao estado real da v0.9.0;
- reorganizada a visão do produto para começar pela estratégia multiárea atual;
- registrado o ciclo v0.9.1 como estabilização documental antes da v0.10.0;
- destacado que v0.10.0, v0.11.0 e v0.12.0 são próximos marcos reais;
- mantidas seções antigas como histórico, sem tratá-las como próximos passos atuais.
- reorganizada a navegação da documentação para a v0.9.1;
- adicionadas entradas MkDocs para histórico do roadmap, arquitetura de prompts, Prompt Registry e
  prompt playbooks individuais;
- clarificado o índice da documentação em torno de visão de produto, roadmap, prompts de IA, regras
  de negócio, dados, fontes e marcos de desenvolvimento;
- documentada a limpeza documental da v0.9.1 como preparação para v0.10.0 AI Structured Extraction
  e Domain Intelligence.

## [0.9.0] - 2026-06-14

### Added

- Assistive Browser Extension Companion em Manifest V3 para capturar, analisar e enviar a vaga
  atual ao tracker;
- Local Companion API restrita a `127.0.0.1:8765`, com token opcional, Pydantic e sanitização;
- importação paginada de candidaturas já realizadas, com lote local de até 500 itens;
- ranking no dashboard dos requisitos mais recorrentes nas vagas candidatas;
- calibração de evidências com pesos, limites por tipo, penalidades e feedback útil/não útil;
- aba avançada **Extensão**, perfil profissional ampliado e extração opcional de currículo por
  Gemini com fallback local;
- fixtures fictícias e regressões para extensão, API local, memória e deduplicação.
- analisador de GitHub, repositórios, projetos e portfólios com dez scores;
- amostragem inteligente de arquivos, análise de README e qualidade de commits;
- modos standalone na extensão e conectado ao SotuHire, com evidências de projeto na memória.
- botão **SotuHire AI** injetado em repositórios e perfis públicos do GitHub;
- modal com score, grade, stack, README, commits, recomendações e ações conectadas;
- pacote validado e documentação de publicação para a Chrome Web Store.

### Changed

- tracker, oportunidades, memória e capturas usam identidade estável por URL normalizada ou
  empresa+título semelhante;
- a mesma vaga encontrada em LinkedIn, Gupy, Indeed, InfoJobs, Nube ou outro portal mantém um
  único cartão com todas as URLs e fontes;
- repetir uma importação atualiza ou reutiliza registros existentes em vez de duplicá-los;
- candidaturas antigas analisadas depois pelo SotuHire permanecem no mesmo cartão `applied`;
- Search Intelligence permite abrir queries no navegador e orienta a captura pela extensão.

### Security

- extensão nunca recebe nem armazena a API Key configurada no SotuHire;
- Local Companion API aceita somente clientes loopback e não faz login, não guarda senha e não
  burla CAPTCHA;
- uso de IA na extensão chama apenas o SotuHire local, que decide o provider configurado.
- Gemini standalone é opcional, usa permissão de host opcional e mantém a chave somente no storage
  local da extensão; a chave nunca é enviada ao SotuHire.

## [0.8.0] - 2026-06-14

### Added

- Career Memory local em JSONL para currículo, projetos, preferências, análises, feedbacks,
  oportunidades e eventos do tracker;
- RAG lexical local com score por keywords, tags, tipo e recência;
- evidências rastreáveis na análise e contexto relevante opcional para Gemini;
- perfil profissional persistente, score de completude e preferências inferidas editáveis;
- aba avançada de memória com busca, export/import, feedback e limpeza;
- personalização de Search Intelligence e Hidden Jobs Radar pela memória;
- registro de vagas às quais a pessoa já se candidatou;
- fixtures, exemplos e regressões de memória/RAG.

### Changed

- modo rápido usa memória relevante automaticamente sem expor painéis complexos;
- dashboard mostra métricas de memória e eventos do tracker;
- Gemini pode aprimorar a análise com um resumo relevante somente mediante opt-in explícito.

### Security

- memória permanece local por padrão em `data/memory/`;
- envio de contexto relevante ao Gemini permanece desativado por padrão;
- exportações privadas permanecem ignoradas pelo Git.

### Authenticated collection

- modos explícitos `PUBLIC_SCRAPING`, `MANUAL_URL`, `USER_ASSISTED_CAPTURE` e `AUTHENTICATED_BROWSER`;
- captura assistida da vaga ou publicação atualmente aberta pela pessoa usuária;
- ações para salvar a vaga atual, analisar e enviar ao tracker;
- roadmap dedicado para extensão de captura assistida;
- crawling autorizado via sessão Chromium já autenticada, com presets para vagas e publicações do LinkedIn;
- limites de itens, páginas/rolagens, intervalo e referência local de autorização;
- inicialização automática de navegador dedicado com perfil persistente e diagnóstico da conexão CDP;

### Authenticated collection changes

- a aba de coleta distingue coleta pública automática, URL única, captura assistida e navegador autenticado;
- fontes configuradas persistem o modo de coleta;

### Authenticated collection security

- captura assistida processa somente o conteúdo visível explicitamente fornecido;
- login, CAPTCHA, checkpoints, auto-apply e envio automático não são automatizados;

## [0.7.0] - 2026-06-13

### Added

- coleta pública por URL, listagem genérica, página de carreira e RSS/Atom;
- registry extensível e fontes configuráveis por TOML;
- cache local, rate limit por domínio, logs e deduplicação;
- store local e normalização de oportunidades para `JobPostingSchema`;
- aba de coleta com preview, teste, coleta, filtro, análise e tracker;
- Search Intelligence e Hidden Jobs Radar acionáveis;
- terceiro teste Gemini pelo caminho real da análise;
- fixtures HTML/XML e regressões da pipeline pública;

### Changed

- modo rápido ficou mais compacto e modo avançado ganhou workflow completo;
- chave e modelo Gemini digitados na sessão são usados imediatamente;
- resultado mostra provider, modelo, fallback e motivo;
- fontes públicas de qualquer domínio podem ser testadas quando `robots.txt` permitir;

### Security

- URLs autenticadas não são coletadas;
- coleta pública usa user-agent identificável, limites, cache e revisão humana;
- auto-apply, spam e bypass de bloqueios continuam ausentes;

## [0.6.0] - 2026-06-13

### Added

- diagnóstico tipado e seguro para chamadas Gemini;
- testes Gemini simples e estruturado separados;
- modelos Gemini selecionáveis no wizard;
- modo rápido em página única e Search Intelligence no modo avançado;
- query builder, plano de fontes e Hidden Jobs Radar sem scraping;
- demo completa local e script Playwright para screenshots;
- screenshots reais do app no README;
- regressões de Gemini, modos, busca, screenshots, skills e demo;

### Changed

- payload estruturado Gemini usa um JSON Schema mínimo compatível;
- layout, hero, badges, sidebar, upload, botões e cards foram compactados;
- skills principais são limitadas e tecnologias restantes ficam recolhidas;
- detalhes técnicos aparecem somente no modo avançado ou no wizard;

### Fixed

- teste Gemini confundindo erro de schema com erro de chave/modelo;
- `400 INVALID_ARGUMENT` sem diagnóstico acionável;
- modo rápido e avançado visualmente equivalentes;
- fluxo de demonstração dependente de múltiplos cliques;

### Security

- diagnóstico nunca mostra a chave completa;
- Search Intelligence e Hidden Jobs Radar não fazem scraping nem chamadas de rede;

## [0.5.0] - 2026-06-13

### Added

- setup guiado do Gemini com status de chave/SDK, teste explícito e salvamento local;
- fluxo automático do modo rápido e análise completa de exemplo;
- currículos, vagas e expected outputs fictícios para validação;
- filtros simples no dashboard por recomendação, modalidade, senioridade, risco e data;
- testes de regressão para setup, fluxo, skills, exemplos, histórico e dashboard;

### Changed

- análise local e Gemini passam a usar mensagens principais amigáveis;
- preferências permanecem opcionais e escondidas no modo rápido;
- contadores do currículo passam a refletir fatos úteis e deduplicados;
- histórico passa a guardar modalidade e senioridade sem salvar textos brutos;

### Fixed

- prefixos como `Linguagens:`, `Ferramentas:` e `Hardware/IoT:` em chips técnicos;
- duplicatas normalizadas e soft skills misturadas às skills técnicas;
- necessidade de editar `.env` manualmente para ativar Gemini;
- análise rápida dependente de clique após cada mudança;

### Documentation

- setup local de Gemini, fluxo automático, fixtures e regressões documentados;
- roadmap, README, provider strategy e guias de desenvolvimento atualizados;

## [0.4.2] - 2026-06-13

### Added

- estrutura interna `ResumeSection` e agrupamento semântico de experiências e projetos;
- aliases para headings técnicos, profissionais, projetos selecionados e formação com cursos;
- fixtures fictícios realistas de currículos e vagas;
- testes de blocos semânticos, aliases de ambiente, fallback e rótulos da UI;
- links clicáveis com rótulos compactos e expansão para listas longas;

### Changed

- provider local passa a ser apresentado como `Análise local`, sem expor `mock` na UI;
- `DEFAULT_AI_PROVIDER` e `GEMINI_MODEL` passam a ser as variáveis documentadas;
- `LLM_PROVIDER` e `LLM_MODEL` permanecem como aliases compatíveis;
- resumo local limitado a evidências curtas de formação, objetivo e skills;

### Fixed

- contagem de experiências e projetos baseada em linhas soltas;
- soft skills longas exibidas como um único chip;
- fallback do Gemini escondido ou pouco claro;
- cards excessivos de experiências e projetos na revisão do currículo;

### Documentation

- semântica do parser e hotfix v0.4.2 documentados;
- instalação e configuração do Gemini atualizadas;

## [0.4.1] - 2026-06-12

### Added

- camada `modules/ui/` com componentes, estilos, layout e páginas reutilizáveis;
- cards e chips para dados detectados do currículo e da vaga;
- detecção de email, telefone, cidade, LinkedIn, GitHub, portfólio, soft skills e idiomas;
- detecção de benefícios e alertas de dados ausentes na vaga;
- testes realistas para parsers e helpers da interface;

### Changed

- `app.py` reduzido à orquestração da aplicação;
- tema Streamlit unificado com contraste explícito em fundo escuro;
- primeiro upload de currículo processado automaticamente;
- vaga colada processada automaticamente antes da revisão;
- termos internos como `unknown`, `mock`, modalidades e senioridades traduzidos na UI;
- resultados reorganizados em score cards e tabs internas;
- versão do projeto atualizada para `0.4.1`;

### Fixed

- texto branco e métricas ilegíveis sobre fundo claro;
- labels, inputs e tabs com baixo contraste;
- resumo do currículo contendo texto bruto excessivo;
- links sem protocolo não detectados;
- experiências e projetos existentes exibidos como zero;
- coincidência falsa de skill `Git` causada por links do GitHub;
- modalidade remota no feminino e contratos de estágio, trainee e freela;

### Documentation

- README atualizado para o fluxo v0.4.1;
- hotfix de UI e parsers documentado;
- relação com tracker, histórico e dashboard registrada;

## [0.4.0] - 2026-06-12

### Added

- fluxo guiado em abas com modo rápido e modo avançado;
- parser automático de vagas com cargo, empresa, localização, modalidade, salário, contrato, senioridade e skills;
- parser de currículos TXT, PDF e DOCX;
- revisão assistida dos dados detectados;
- camada de IA estruturada com provider mock/local e Gemini opcional;
- fallback local quando o provider externo não está disponível;
- Resume Tailor com resumo, bullets, ordem de seções, keywords, warnings e evidências;
- exportações de análise em JSON e Markdown;
- exportação do Resume Tailor em Markdown;
- persistência local JSON com confirmação de privacidade;
- Job Tracker com status tipados;
- histórico local e dashboard inicial;
- testes de parsers, provider, exporters, storage, tracker e dashboard;

### Changed

- interface Streamlit redesenhada para parecer produto;
- `DEFAULT_AI_PROVIDER` alterado para `mock`;
- dependências PDF/DOCX mantidas leves;
- versão do projeto atualizada para `0.4.0`;

### Fixed

- fluxo excessivamente manual da v0.1;
- ausência de histórico e métricas;
- ausência de fallback estruturado para IA;

### Documentation

- roadmap consolidado até v0.4;
- arquitetura de parsers e storage documentada;
- auditoria de prontidão v0.4;
- README, MkDocs e guias de desenvolvimento atualizados.

## [0.1.0] - 2026-06-12

### Added

- schemas Pydantic para análise, preferências, Resume Tailor e JSON Resume;
- análise currículo x vaga com Match Score e gaps;
- Opportunity Fit Score baseado em preferências;
- ATS Score simples e explicável;
- Risk Score e recomendação determinística;
- Resume Tailor em modo sugestão;
- regras anti-invenção apoiadas por evidências;
- interface Streamlit do MVP Core;
- testes focados para schemas e regras de negócio;

### Changed

- dependências padrão mantidas leves para a v0.1;
- roadmap alinhado ao SotuHire v0.1 — MVP Core;

### Fixed

- ordenação de imports detectada pelo Ruff;
- navegação MkDocs para documentos importantes;
- inconsistências entre README, roadmap e implementação atual;

### Documentation

- documentação revisada e expandida sem reduzir docs existentes;
- README atualizado com visão, limites, arquitetura, comandos e status;
- auditoria de prontidão v0.1;
- metadados, tópicos GitHub e hashtags recomendados.
