# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

## Unreleased

### Documentation

- alinhado `docs/01-product/roadmap.md` ao estado real da v0.9.0;
- reorganizada a visão do produto para começar pela estratégia multiárea atual;
- registrado o ciclo v0.9.1 como estabilização documental antes da v0.10.0;
- destacado que v0.10.0, v0.11.0 e v0.12.0 são próximos marcos reais;
- mantidas seções antigas como histórico, sem tratá-las como próximos passos atuais.

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
