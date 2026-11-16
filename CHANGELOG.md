# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

## Unreleased

## [2.1.0] - 2026-11-16

Redesign da interface (identidade 2.1), Perfil → Currículo Mestre sem redigitação e o trabalho da
auditoria independente de 2026-11 (ver `docs/00-audit/2026-11-independent-assurance-audit.md` e
[notas da release](docs/releases/v2.1.md)). Extensão 0.10.1. Schema SQLite continua 8.

### Adicionado

- `scripts/verify_extension_modes.py`: carrega o ZIP da extensão num Chromium real e usa o popup de
  verdade nos três modos (independente, com Local Companion, integrado ao site e à API), com
  serviços num diretório descartável e fixtures para GitHub, Gemini e OpenAI que recusam o que as
  APIs reais recusam. 52 verificações na 0.10.1.
- `scripts/capture_readme_media.py`: capturas do README, GIF e vídeo WebM gravados do build de
  produção em modo de exemplo.
- `scripts/dast_local_api.py`: sondas dinâmicas contra a API local rodando (Host forjado, origem
  estranha e preflight, rotas sem sessão, prova de pareamento forjada, corpo grande sem sessão e
  tamanho declarado acima do limite, travessia no download de backup, vazamento de caminho em erros).
  Com `--bootstrap` (instância descartável) pareia uma sessão como o app web e repete a travessia
  com ela, com controle positivo (o arquivo legítimo baixa): 27 sondas.
- `scripts/verify_extension_in_chromium.py`: empacota a extensão, carrega o ZIP distribuído num
  Chromium real e verifica service worker, popup sem erros e a captura (o mesmo fluxo do popup)
  numa página do GitHub servida offline; com o ZIP sem `content.js` o relatório falha.
- Gate de experiência (CP-UX06): suíte E2E aprovada em Chromium, Firefox e WebKit; Web Vitals do
  build de produção medidos com script versionado (`apps/web/scripts/measure-vitals.mjs`); harness
  de mutação adversarial de UI (`apps/web/scripts/ui-mutants.py`, 10 mutantes, 9 mortos, 1
  equivalente). O modo de exemplo do Application Lab mostra uma afirmação sem evidência com
  "Aceitar" desabilitado.
- Tela inicial na identidade nova (CP-UX05): marca própria, hero marinho→petróleo, números em sans
  tabular. `TextField` compartilhado substitui três cópias locais de campo.
- Aprovações recompostas (CP-UX04): filtros por etapa da decisão, risco e status em português,
  prévia campo a campo (o que muda, hoje e depois de executar), como desfazer sempre visível, botões
  com estado pendente e falhas ditas. Copilot com os nomes e destinos do Cockpit e caminho até a
  fila depois de criar uma proposta. Configurações dizem para onde vai o texto de cada provider.
  Application Lab separa orientação de mudança e mostra o estado da sessão em português.
- Radar, Fontes e Tracker recompostos (CP-UX03). Tracker: funil com proporção e filtro por etapa,
  follow-ups vencidos em destaque, cartões sem informação repetida e com "Preparar candidatura" quando
  o anúncio foi preservado, filtro sem acento, lista como padrão no celular com troca de visualização
  visível. Radar: um painel com a explicação e uma faixa de indicadores que leva às seções, no lugar de
  4 cartões iguais. Fontes: navegação por seções e indicadores da caixa de entrada sem zero falso.
- Busca nos dados (`/api/v2/search`) sem acento, com todas as palavras, sobre evidências, portfólio,
  fatos do Perfil (exceto sensíveis) e candidaturas; resultados ordenados por relevância. A paleta
  mostra o tipo e o subtítulo de cada resultado.
- Perfil e Resume Studio recompostos (CP-UX02). Perfil: hero com nome, headline, áreas e parcela de
  fatos confirmados; abas "Fatos e evidências", "Identidade e objetivos" e "Importar" com link direto
  (`/profile?tab=…`); fatos com tipo e origem legíveis, estado de confirmação, "Confirmar" para o que
  está pendente, edição no lugar e remoção com confirmação; "Adicionar fato" em diálogo com validação;
  identidade com aviso de alterações não salvas e "Descartar". Resume Studio: cabeçalho da variante
  (vínculos com o Perfil, páginas, pendências), barra de ferramentas agrupada, estado de salvamento
  anunciado, preview em papel, importação recolhida. Componente `Field` compartilhado (rótulo ligado ao
  controle, dica e erro anunciados).
- Fatos alterados no Perfil depois de entrarem no Currículo Mestre aparecem com o texto do Mestre e o
  do Perfil lado a lado; a pessoa escolhe quais atualizar (`POST /resume-studio/master/profile-refresh`).
  O Perfil nunca é escrito a partir do Mestre.
- Variantes com controle de versão: `PATCH /resume-studio/variants/{id}` aceita `expected_updated_at`
  e responde 409 se a variante foi salva em outra aba; o editor para o autosave e pergunta qual versão
  fica.
- Primeira visita em 2 etapas (antes 8): idioma, tema e princípios; depois os caminhos de início.
- Correção visual do redesign (CP-UX01B): barra lateral marinho também no tema claro (e no menu
  "Mais" e na barra de jornadas do celular), com o item atual em petróleo; superfícies em camadas
  (`canvas`, `surface`, `surface-raised`, `surface-muted`, `surface-accent`, `surface-interactive`)
  e sombras suaves; hero do Cockpit com gradiente marinho→petróleo e anel de cobertura;
  indicadores com ícone e cor por tipo; forças comprovadas e lacunas diferenciadas; primeiro passo
  como ação principal. Serifa só em títulos e no hero; números em sans tabular. Marca e favicon em
  selo petróleo→azul. Nada do comportamento do CP-UX01 mudou (jornadas, busca, estados, traduções,
  destinos).
- Redesign, primeira fatia (CP-UX01): identidade "dossiê de carreira" (papel e tinta, verde-pinho
  para evidência confirmada, ocre para o que espera revisão, vermelho-selo para o que espera a
  pessoa), fontes OFL empacotadas que funcionam offline (Source Serif 4, IBM Plex Sans e Mono),
  marca e favicon próprios no lugar do ícone genérico. A navegação passa a ser por jornada (Hoje,
  Quem eu sou, Currículos, Oportunidades, Candidaturas, Sistema) a partir de um registro único de
  telas, com a jornada atual aberta; no celular, barra inferior com as jornadas e "Mais". Cabeçalho
  com a jornada como sobrelinha e o título inteiro também no celular. Todas as telas mantêm o
  endereço.
- Busca única (Ctrl+K) sobre todas as telas, sem acento, com ranking, destaque do termo, telas
  visitadas recentemente, dados locais com cancelamento da requisição anterior e mensagens de
  carregamento, falha, modo de exemplo e "nada encontrado". A Central de Ajuda usa o mesmo ranking.
- Cockpit: próximos passos com nome em português e destino certo (preparar entrevista abre
  Entrevistas, evidências pendentes abre Evidências; antes todos levavam a Aprovações), faixa de
  indicadores no lugar de quatro cartões idênticos, estados de carregamento, erro e vazio.
- Baseline do redesign (CP-UX00): a captura de UX cobre as 25 rotas reais (faltavam 3), 4 larguras
  (1440, 1024, 390, 360), tema claro e escuro e en-US, e um spec novo grava 10 estados de uso
  (primeira visita, busca, navegação mobile, API fora do ar, primeiro uso do Resume Studio, Copilot).
  `scripts/build_ux_gallery.py` gera a galeria versionada e o manifesto com o hash de cada captura.
  Direção de design em `docs/08-frontend/design-direction-2026-11.md` e ADR 006.
- Resume Studio monta o Currículo Mestre a partir do Perfil Universal (só fatos confirmados e não
  sensíveis, com a origem de cada entrada) em vez de pedir o currículo de novo, e lista fatos
  confirmados depois no Perfil para a pessoa escolher quais entram. Nada volta da variante para o
  Perfil. Ver `docs/00-audit/2026-11-data-authority-map.md`.
- Provider Anthropic (Claude) com Claude Haiku 5.5 como modelo padrão: saída estruturada validada
  pelo schema do prompt, chave só no backend (Configurações → IA ou `ANTHROPIC_API_KEY`), mesma
  política de opt-in, erros e novas tentativas dos outros providers. Validado por testes de contrato;
  nenhuma chamada real foi feita nesta revisão.

### Segurança

- A API local respondia 401/403/429 sem cabeçalhos CORS, porque o middleware de segurança fica do
  lado de fora do CORS. O navegador escondia o 401, e o pareamento da interface web (que começa
  justamente com um 401) nunca acontecia. As rejeições para uma origem autorizada agora trazem os
  cabeçalhos; origens não autorizadas continuam sem eles.
- O Copilot revalida status, expiração e `dependency_hash` da proposta dentro da mesma transação
  `BEGIN IMMEDIATE` que grava o efeito, o registro de execução, o status e o audit; aprovar e depois
  mudar o estado de carreira ou deixar expirar não executa mais a ação.
- `undo` de arquivamento é condicional: se a evidência foi editada depois da execução, retorna
  conflito em vez de sobrescrever a edição.
- O service worker da extensão aceita mensagens privilegiadas só das páginas da própria extensão e
  monta URLs apenas para rotas conhecidas do Local Companion na origem pareada; um content script não
  consegue mais desviar o token para outra URL.
- Pisos de dependências vulneráveis elevados (`pypdf>=6.21.4`, `python-dotenv>=1.2.2`) e lockfile
  web corrigido por `npm audit fix` (incluindo a crítica em `seroval`).
- A checagem de campos com cara de credencial antes de chamadas de IA e capturas tem um único dono
  (`modules/security`); duas das quatro cópias não bloqueavam `headers`.
- Local Companion autentica antes de ler o conteúdo: o corpo de uma rota protegida só é
  decodificado e interpretado depois da credencial, e o servidor HTTP passou a só limitar e ler
  bytes. Antes, um corpo inválido sem credencial respondia 422 (o JSON era interpretado antes da
  autenticação, em duas camadas) e um `[]` em `/pairing/complete` derrubava o handler com
  `AttributeError`. Agora: 401 sem credencial, qualquer que seja o corpo; 413 acima do limite
  antes de tudo; 400 para corpo que não é JSON UTF-8 e 422 para JSON que não é objeto, profundo
  demais ou com lote acima do limite, só depois da autenticação. Caminho público com método
  errado responde 405.

### Corrigido

- Tracker: uma candidatura criada enquanto a lista inicial ainda carregava sumia da tela, porque a
  resposta da listagem pedida antes substituía o cache (SH-NEW-041). Reproduzido em teste com
  respostas controladas; a criação agora invalida a listagem (que cancela a requisição em voo) e o
  modo de exemplo guarda as candidaturas criadas na sessão.
- Resume Studio: adotar um currículo reimportado substituía o Currículo Mestre em uso sem aviso.
  A API recusa (409) a troca do Mestre por outro currículo sem `replace_existing`, e a confirmação
  precisa nomear o Mestre exibido; a tela mostra o que será substituído e pede confirmação. O Mestre
  anterior não é apagado.
- Banco local: o primeiro acesso concorrente a um banco novo (várias requisições, ou Local
  Companion e API no mesmo diretório) rodava as migrações duas vezes e podia responder 500
  ("Schema divergente"). Migração e verificação agora são serializadas por um lock de arquivo
  entre threads e processos.
- Local Companion: recapturar uma página sem mudança marcava análises, variante e kit como
  desatualizados ("A vaga mudou"), porque o horário da captura entrava no hash do snapshot. Vagas e
  editais iguais agora reaproveitam o snapshot.
- Extensão 0.10.1: a análise "OpenAI própria" enviava `response_format` à Responses API, que a
  rejeita, e caía sempre no fallback local; uma falha na análise de projeto deixava o popup em
  "Processando…" para sempre; com "IA configurada no SotuHire" (o padrão) e nada rodando, a análise
  agora devolve o relatório local com o fallback declarado.
- Testes: a suíte força `SOTUHIRE_DATA_DIR` e `SOTUHIRE_BENCHMARK_DATABASE` para uma pasta
  descartável (antes, um `SOTUHIRE_DATA_DIR` exportado recebia escritas) e falha se algo em
  `data/` ou `benchmarks/` do checkout mudar.
- Dados locais: cinco stores (perfil de carreira legado, oportunidades, análises de projeto,
  cache de scraping, token de instalação) usavam `data/...` relativo ao diretório de trabalho
  e ignoravam `SOTUHIRE_DATA_DIR`. A suíte de testes regravava o perfil de carreira do checkout
  do desenvolvedor, e a API de extensão lia análises fora do diretório configurado. Os padrões
  agora ficam no diretório de dados configurado (SH-NEW-040).
- DAST: a sonda de corpo grande sem sessão contava uma conexão derrubada como recusa correta; agora
  envia 64 KB de 6 MB por socket e só passa ao ler a linha `401`; sem resposta é inconclusivo e
  falha. A sonda de prova de pareamento forjada não mandava `Origin` e parava no 403 da origem sem
  chegar à prova; agora usa uma origem permitida e exige o 401 da checagem da prova.
- Contrato cliente × API: a cópia versionada do OpenAPI mudava com a versão do FastAPI/Pydantic
  instalada (o CI instala as mais novas compatíveis) e falhava sem mudança de API. Passa a ser uma
  visão do contrato (corpos de requisição, respostas 2xx e os schemas alcançados; sem títulos,
  descrições e defaults), idêntica nas duas combinações testadas; um campo novo na requisição ou um
  campo renomeado na resposta continuam mudando a visão (testes).
- Backup: arquivos de backup tinham nome com resolução de segundo e eram sobrescritos sem aviso. Ao
  restaurar um backup criado no mesmo segundo, o backup de segurança da própria restauração
  substituía o arquivo escolhido (restauração falhava com "Arquivo ZIP inválido" ou trazia o estado
  atual). Duas exportações no mesmo dia também se sobrescreviam. Nomes agora nunca colidem e um
  arquivo existente nunca é sobrescrito.
- API Real: "Adicionar ao perfil" a partir de um texto importado respondia 422 sempre (o cliente
  enviava o item de rascunho inteiro, com `item_id` e datas que o contrato não aceita). Achado pelo
  teste de contrato novo: `src/lib/api/contract.test.ts` envia os corpos das escritas que as telas
  fazem com objetos de domínio pelo cliente real e os confere contra o OpenAPI versionado
  (`scripts/export_openapi.py`; o pytest acusa se a cópia ficar desatualizada).
- Tela inicial: o título pulava ~60 px quando a fonte serifada carregava (CLS 0,14 → 0,002), com
  fallback de métricas medidas por peso.
- Testes: quatro verificações não podiam falhar (checagem de "Aprovar tudo" antes de a fila carregar,
  em dois specs; `toHaveCount(0)` sobre toasts, que espera o toast sumir, em três specs).
- Modo de exemplo: aprovar, rejeitar, executar, desfazer e criar proposta não mudavam nada na tela.
- Aprovações: sem estados de carregamento, erro e vazio (a página ficava em branco numa falha); falha
  de transição não era dita.
- Tracker em lista: o seletor de status de cada candidatura não tinha nome acessível.
- API Real: criar candidatura pelo Tracker respondia 422 sempre (o frontend enviava `source`, que o
  contrato não aceita; o campo da API é `source_url`). Corpo montado com os campos do contrato e
  teste que falha se um campo desconhecido voltar.
- Configurações de IA: escolher um provider antes de a configuração salva carregar (ou durante um
  refetch) era desfeito e o campo da chave voltava a ficar desabilitado.
- Resume Studio: erro diferente de 404 ao abrir ficava em "Abrindo…" para sempre; rascunho do
  navegador restaurado não era salvo; importação gravava o Mestre numa chave de cache errada; toast
  dizia "JSON_RESUME".
- Perfil: remover um fato não pedia confirmação; tipos e origens apareciam como identificadores
  (`higher_education`, `demo_resume`).
- Consultas não repetem mais respostas 4xx: o primeiro uso do Resume Studio (404 "Mestre ainda não
  existe") mostrava "Abrindo seu estúdio…" por cerca de 7 s antes do onboarding, e o E2E
  correspondente falhava sob carga (2 de 3 execuções). Política em `src/lib/api/retry.ts` (408, 429 e
  5xx repetem; conexão recusada repete uma vez) com testes. A camada v2 passa a lançar
  `ApiHttpError` com o status.
- Gráfico "Status do Kanban" (Inteligência): cada setor tem nome acessível (`svg-img-alt`).
- Modo API Real: nenhuma chamada do Career Copilot (Cockpit, aprovações, evidências, portfólio e
  busca) saía do navegador; a camada v2 passava uma URL `/api/v2` ao pareamento, que só aceita
  `/api/v1`, e falhava antes da rede (desde `880a5f1`, 2026-08-10). Verificado contra a API real:
  pareamento, Cockpit, busca e primeiro uso do Resume Studio.
- Com a API local fora do ar, o Cockpit mostrava "Carregando…" e zeros como se fossem dados; agora
  mostra a falha, um aviso global com "Dados de exemplo" e "Gerenciar conexão", e tenta de novo só
  uma vez em erro de conexão.
- Tema escuro: 28 nós de contraste insuficiente por largura de tela (`text-*-foreground` sobre
  tons claros) migrados para as variantes `-strong`.
- Teste E2E do Radar que passava sem verificar nada: a expressão `/…|lida|Modo Demo/` casava com
  "Compatibi**lida**de" no menu lateral. As checagens de toast agora olham só o toast e a mensagem
  de cada ação.
- Local Companion: as rotas autenticadas viraram uma tabela explícita, testada rota a rota (só
  `/health` e o pareamento são públicos); rota conhecida com método errado responde 405 e rota
  desconhecida continua escondida atrás da autenticação.
- O teste da fronteira da Companion percorre a tabela de rotas que o app usa (não uma cópia), fixa
  o conjunto de caminhos públicos e confere que todo caminho chamado pela extensão está declarado.
- Aplicar fatos do Perfil ao Currículo Mestre é idempotente: um ID repetido no pedido gerava
  entradas duplicadas, e repetir um pedido que já tinha dado certo respondia 422. Agora o ID conta
  uma vez e o que já está no Mestre não muda nada (o retry responde 200 com o mesmo currículo).
- Gravações do Currículo Mestre baseadas numa cópia antiga respondem 409 em vez de apagar o que
  outra aba ou a aplicação de fatos do Perfil tinha gravado: a aplicação de fatos sempre confere a
  versão, e `PUT /resume-studio/master` confere quando recebe `expected_updated_at`. A conferência
  e a gravação ficam na mesma transação `BEGIN IMMEDIATE`. A tela de atualizações do Perfil recarrega
  o Mestre e a lista ao receber 409.
- Application Lab: aceitar uma sugestão sem edição falha quando o texto afirma registro profissional
  (os 26 conselhos e registros conhecidos, como CRM, OAB e COREN) ou pós-graduação (doutorado, mestrado, MBA,
  especialização) que não aparece no texto substituído nem no Currículo Mestre confirmado. Antes, bastava
  a sessão ter alguma evidência selecionada. Um texto editado pela pessoa continua sendo dela.
- Tarefas criadas pelo Copilot quebravam a listagem de tarefas da Career API (HTTP 500).
- `create_task` retornava `created: true` mesmo quando a tarefa já existia; propostas rejeitadas ou
  expiradas eram devolvidas ao repropor; a aresta salva retornava um id diferente do persistido.
- O catálogo de prompts marcava `career_advice_v1`, `github_profile_analysis_v1` e
  `portfolio_gap_analysis_v1` como implementados; o único arquivo que os chamava não era importado por
  nada. Agora aparecem como registrados sem consumidor, e o gerador só conta como consumidor um
  arquivo que o código de produção importa.
- Salvar um provider de IA sem escolher modelo gravava o modelo do Gemini para qualquer provider
  (OpenAI seria chamado com `gemini-2.5-flash`); agora vale o padrão do provider escolhido.
- `.env.example` listava 24 variáveis, das quais só 4 eram lidas pelo código, e omitia outras em uso
  (`SOTUHIRE_DATA_DIR`, `OPENAI_MODEL`, configuração da API local); agora lista só o que existe.
- Resume Studio sem Currículo Mestre mostrava erro com "tentar novamente" em vez do primeiro uso.
- Um rascunho antigo guardado no navegador substituía a variante salva no servidor ao reabrir o
  Resume Studio; agora só vence se for da mesma variante e mais novo, e é apagado ao salvar.
- Acessibilidade: o axe (WCAG 2.x A/AA) apontava 20 nós críticos e 309 sérios em 22 rotas; agora
  zero. Texto em cores semânticas usa tokens de contraste próprios, campos ganharam nome acessível
  e a busca universal usa o texto visível como nome.
- `due_at` de tarefas agora exige fuso horário e é normalizado para UTC na API e no frontend.
- Fingerprint do Career State passa a incluir oportunidades e resultados recentes.
- Página Carreira: lembrete pede a tarefa relacionada explicitamente; o modo demo mostra o que foi
  salvo na sessão em vez de não fazer nada.

### Alterado

- `ensure_database()` não repete as verificações completas de integridade a cada chamada de
  repositório quando o arquivo não mudou: `list_nodes` com 2.000 evidências caiu de 18 para 5,5 ms;
  uma chamada em cache custa 0,5 ms contra 19,6 ms da verificação completa. A identidade do arquivo
  usa tamanho, data e hash do cabeçalho do banco e tamanho e cabeçalho do WAL (os sais mudam quando
  o WAL reinicia, então uma escrita que reaproveita quadros sem crescer é vista); a verificação vale
  no máximo 10 minutos (dano que preserva tamanho, data e cabeçalhos é pego então) e restaurar um
  backup a descarta.
- Instalação padrão sem Streamlit e sem pandas: a interface Streamlit (modo legado/dev desde a
  v1.4) vai para o extra `legacy-ui`; o fechamento de runtime caiu de 51 para 28 pacotes.
- Dependências vivem só no `pyproject.toml` com extras `ai`, `browser`, `docs`, `legacy-ui` e `dev`;
  as mensagens de instalação da UI e da API apontam para eles.
- Licença declarada como expressão SPDX com `LICENSE` dentro do wheel (o formato antigo deixa de
  ser aceito pelo setuptools em 2027-02-18).
- SBOM CycloneDX inventaria o fechamento transitivo Python e todo o lockfile npm, com arestas de
  dependência, e é verificado no CI; uploads de artefatos obrigatórios falham se o arquivo faltar.
- CI roda todas as specs E2E em Chromium, a instalação limpa realmente cria um venv novo e
  `npm audit` bloqueia em severidade crítica.
- Dependabot agrupa CodeQL e atualizações minor/patch por ecossistema.
- Atualizações de dependências revisadas: Ruff 0.17.3, CodeQL 4.38.3, upload-artifact 7.0.2,
  deploy-pages 5.0.1 (pins por SHA conferidos contra as tags), Tailwind 4.3, Radix tabs/label e
  Prettier 3.10; `@axe-core/playwright` como dependência só de desenvolvimento.

### Obsoleto

- `POST /api/v1/profile/import-lattes` é alias de `POST /api/v1/profile/lattes/draft` e aparece como
  `deprecated` no OpenAPI.

### Removido

- Utilitários CSS `grid-bg` e `glass`, sem consumidor depois do CP-UX05.
- `docs/requirements/*.txt` (duplicavam o `pyproject.toml` e já divergiam dele).
- Código sem nenhum consumidor: `modules/storage/repositories` (CRUD genérico nunca adotado),
  `modules/alerts`, `modules/sources/registry.py`, módulos de tracker/currículo/perfil/busca sem
  importador, dez métricas de avaliação de IA e helpers isolados. Detalhes e prova por item em
  `docs/00-audit/2026-11-dead-dedupe-triage.md`.
- Segunda camada de código sem consumidor, exposta pelas remoções anteriores: `modules/ai/guidance.py`,
  o reexport `modules/ai/provider.py`, `modules/rag`, `modules/sources/base.py`,
  `modules/core/schemas.py`, `matching/exceptions.py`, `memory/memory_index.py` e módulos de busca e
  portfólio usados só por testes (`query_generator`, `post_detector`, `source_ranker`, `portfolio_score`).
- Scripts de captura de screenshots de versões passadas (v1.1, v1.9.8, v1.9.9, v1.10.1, v1.11.0).

## [2.0.0] - 2026-08-10

### Adicionado

- Evidence Graph e portfólio multidisciplinar em SQLite schema 8.
- Career State e Next Best Actions determinísticos, com confiança separada.
- Career Copilot, planos, registry fechado, ProposedActions, approval, audit e undo.
- Career Cockpit, Evidence Inbox, Approval Queue, Portfólio e busca Ctrl/Cmd+K.

### Segurança e compatibilidade

- Writes importantes exigem proposta individual e aprovação humana; tool injection, replay, stale,
  expiry e input inválido possuem testes dirigidos.
- App/Companion 2.0.0; extensão 0.10.0 sem bump vazio; contratos v1 preservados e API v2 adicionada.
- Não foi criada release/tag v1.11.1.

## [1.11.0] - 2026-08-10

### Adicionado

- Políticas determinísticas de matching para 13 domínios, analytics explicável e updater explícito
  com preview/apply/status/rollback para CBO, QBQ, ESCO e O*NET.
- Interoperabilidade opt-in com Ollama, LM Studio e endpoints OpenAI-compatible, incluindo health
  explícito e matriz completa de 25 AiTasks.
- Settings reorganizado em Geral, Idioma, Aparência, IA, Privacidade, Dados, Extensão,
  Notificações, Ajuda e Sobre.

### Segurança

- Transporte SSRF-safe conecta ao mesmo IP validado e revalida redirects; boundaries de URL,
  Origin, paths, restore e argumentos do Chromium foram endurecidos.
- GitHub Actions/CodeQL usam runtime atual e pins SHA; frontend resolve nanoid 3.3.18 sem override.
- PyMuPDF AGPL/comercial foi substituído por pypdf e ReportLab BSD.

### Alterado

- Aplicação/Companion 1.11.0; extensão permanece 0.10.0 e SQLite permanece schema 7 porque não houve
  mudança material nesses contratos.
- Documentação, roadmap, arquitetura, regras, auditorias e evidência de release foram sincronizados.

## [1.10.1] - 2026-08-10

### Adicionado

- Conectores públicos Greenhouse, Lever, `schema.org/JobPosting` e RSS/Atom com proveniência, identidade canônica, deduplicação e ranking local explicável.
- Camada versionada de normalização de ocupações e competências para CBO, QBQ, ESCO e O*NET, com manifestos, hashes e revisão humana de mappings.
- Workflows persistentes de entrevista, banco STAR, perguntas/respostas, follow-up em rascunho, tarefas, lembretes, Career Plan e exportação ICS explícita.
- Frontend com preferências adaptativas `pt-BR`/`en-US`, tema claro/escuro/sistema, ajuda contextual, central de ajuda, onboarding e novas jornadas de entrevista e carreira.
- Nove tasks de IA para os novos workflows, todas ligadas ao registry, prompt versionado, schema, propósito mínimo de Career Context e fallback local.
- Schema SQLite 7, documentação de arquitetura/regras/migração, evidências visuais atuais e extensão MV3 0.10.0.

### Alterado

- Dashboard em API Real passa a exibir somente scores persistidos; caches e pareamento do frontend ficam isolados por origem/base URL.
- JSON Resume passa a mapear semanticamente todas as seções oficiais suportadas, preservar extensões e manter registros profissionais fora de `certificates`.
- Navegação, headings, drawers e controles compartilhados foram reorganizados para jornada, teclado, mobile e zoom, sem fonte web remota.
- README, índices, escopo atual, roadmap, catálogo de prompts, matriz de capacidades e documentação de release foram alinhados à v1.10.1.

### Segurança e integridade

- Detecção/redaction de credenciais Gemini modernas `AQ.` cobre arquivos, ZIPs, traces, diagnósticos, respostas e service worker sem marcar texto comum indiscriminadamente.
- Pairing local usa bootstrap fora de banda, cookie HttpOnly, CSRF rotativo, TTL e allowlist exata da extensão; URLs da API web ficam restritas a loopback.
- Proteção SSRF rejeita userinfo, portas inesperadas, IP/DNS não global e revalida cada redirect.
- Follow-up permanece rascunho, ICS é somente download e nenhuma ação de terceiro é enviada automaticamente.

### Limitações conhecidas

- Algumas telas históricas ainda possuem conteúdo interno apenas em PT-BR; shell, navegação, ajuda e fluxos novos respondem ao locale.
- Bases oficiais completas não são baixadas nem redistribuídas automaticamente; importação e mappings permanecem versionados e revisáveis.
- Stores JSON/JSONL legados continuam ativos para contratos antigos; os novos domínios usam SQLite sem dual-write oculto.
- Providers externos dependem de rede, credencial e quota. Na validação final, Gemini executou casos reais; OpenAI foi bloqueado por quota insuficiente e não foi tratado como aprovação.

## [1.9.9] - 2026-08-07

### Adicionado

- Ingestão revisável de PDF, DOCX, HTML, TXT e JSON Resume, com documento canônico, proveniência por bloco e adoção explícita no Currículo Mestre.
- Resume Studio com variantes rastreáveis, Professional Assets, Application Kit de oito itens e exports reais em PDF, DOCX e JSON Resume.
- `EvidenceScope`, estados de revisão e `ApplicationAnalysisBundle` com Match, ATS, readiness e Tailor independentes.

### Segurança e integridade

- APIs loopback protegidas por pairing/sessão, CSRF, Host/Origin/CORS e limites de recursos; scanner/redactor cobre credenciais Gemini `AQ.` contextualizadas.
- Tracker e Application Lab transacionais/idempotentes, artefatos dependentes marcados como `stale`, stores JSON corrompidos enviados a quarantine e Perfil Universal reconciliado com o legado.
- Schema SQLite 6, migração 5→6 explícita com dry-run/backup/verify e extensão MV3 0.9.5 com handoff somente por IDs.

### Limitações conhecidas

- PDF somente-imagem requer revisão manual; não há OCR automático.
- Providers externos continuam opt-in e dependem de credencial, quota e rede; o caminho local não depende deles.

## [1.9.8] - 2026-07-28

### Adicionado

- Application Lab persistente em dez etapas, com readiness multiárea, sugestões revisáveis, variante, kit, plano, snapshots e Tracker.
- Resume Studio com Currículo Mestre, editor, reordenação, undo/redo, autosave, diff, quatro templates ATS-safe, preview e JSON Resume.
- Migration 5 e APIs paginadas para sessões, relatórios, currículos, variantes, exports e artefatos de candidatura.
- Suites externas `provider-diagnostic` e `provider-structured-output`, além de evidências visuais desktop/mobile e GIF da jornada.

### Alterado

- Extensão 0.9.4 captura/deduplica a vaga e abre o Lab somente com `capture_id` e `job_snapshot_id`.
- Gemini/OpenAI compartilham taxonomia de erros, retry limitado com `Retry-After`, reparo controlado e fallback explícito.

### Corrigido

- OpenAI 429 diferencia quota insuficiente de rate limit, billing e project limit; bloqueio de conta não vira aprovação.
- Schemas Gemini são reduzidos ao subconjunto suportado e não recebem defaults silenciosos após resposta inválida.
- Superfícies de gradiente do Application Lab mantêm contraste correto.

### Limitações conhecidas

- PDF/DOCX permanecem pendentes para a v1.9.9; preview e JSON Resume são funcionais.
- A rodada externa final encontrou rate limit/alta demanda no Gemini e quota insuficiente no OpenAI; nenhum caso foi ocultado ou usado para baseline inválido.

## [1.9.7] - 2026-07-14

### Adicionado

- Registry comum de 16 tarefas de IA, governança de prompts e defesa compartilhada contra prompt injection.
- AiRunStore 2.0 com latência, tokens, custo disponível, schema, contexto, evidência, fallback, retenção e paginação seguros.
- Golden datasets fictícios com 12 domínios, casos adversariais e métricas estruturais, de evidência, calibração, utilidade, operação e deduplicação.
- Benchmark reprodutível com mocks, local, providers opt-in, seed, resume, regressão e baselines sanitizados.
- Feedback humano, Outcome Learning não causal, APIs paginadas e painel `/ai-quality`.
- Migration 4 para feedback, benchmarks, resultados e eventos/métricas de outcome.

### Alterado

- Chamadas de IA passam a registrar provider/modelo solicitado e usado, prompt, fallback e métricas disponíveis sem persistir conteúdo pessoal integral.
- Gemini e OpenAI capturam uso/timing quando retornado e validam structured output; custo desconhecido permanece ausente.
- Extensão 0.9.3 adiciona feedback de análise GitHub vinculado somente a trace seguro.
- Catálogo de prompts inclui suíte, golden cases, benchmark, baseline e providers testados.

### Segurança

- Conteúdo importado é delimitado como não confiável, erros são sanitizados e segredos são excluídos de traces, benchmarks e feedback.
- Testes externos aceitam somente variáveis temporárias específicas e fixtures fictícias.

## [1.9.6] - 2026-07-12

### Adicionado

- Repository abstraction para JSON, JSONL e SQLite, com migrações locais versionadas.
- Migração dry-run/apply/verify com backup prévio, importação transacional, dedupe conservador e arquivos legados preservados.
- Backup, export, restore checksummed e data health, disponíveis também no painel de Privacidade.
- Snapshots imutáveis de vaga, currículo, análise e edital, ligados às candidaturas do Tracker.
- `AiRunStore` com provider/modelo/prompt/fallback/evidências sem armazenamento de segredos.
- Manifesto de capacidades, matriz de integração e catálogo de prompts gerados/verificados.
- Fundação de ingestão PDF/DOCX/HTML/TXT/JSON e interoperabilidade revisável com JSON Resume.
- Handshake de extensão/Companion/API, fila com retry/backoff/limite/export/import e prioridade para JSON-LD `JobPosting`.
- Testes de repositories, migração, snapshots, restore, health, extensão e integração de dados.

### Alterado

- Tracker passa a preservar stage history e vínculos com vaga, currículo e análises usados.
- Identidade de Perfil, memória, vaga, edital e GitHub preserva referências sem colapsar fatos distintos do mesmo container.
- Career Context mantém confiança, confirmação, sensibilidade e `source_ref`; ATS/Tailor/Radar não promovem item não confirmado a fato seguro.
- Permissões de IA de Perfil, Lattes, Extensão e Notificações passam a ser aplicadas pelo runtime.
- Frontend preserva warnings, request ID, trace, candidatos GitHub e contexto do Tracker.
- README, roadmap, índices, arquitetura de dados e documentação da extensão foram reorganizados como referências atuais.
- Versões do app, API e frontend alinhadas; extensão atualizada de forma independente por conter mudanças funcionais.

### Corrigido

- Fallback OpenAI no GitHub não é mais marcado como fallback Gemini.
- Health check de SQLite é realmente read-only, inclusive em banco pré-schema ou corrompido.
- Restore valida formato, versão, checksum, schema, integridade e foreign keys do SQLite antes de gravar.
- Manifesto de backup registra schema real e versão máxima suportada.
- Timelines legadas de edital são normalizadas para o contrato de snapshot.
- FKs de snapshots usam restrição de exclusão coerente com imutabilidade.
- Scripts de dados funcionam quando executados diretamente fora da raiz do repositório.

### Segurança

- Chaves expostas não foram usadas; testes externos continuam opt-in e skipped sem chave temporária nova.
- Backup/export excluem secrets por caminho, nome e padrões de conteúdo; pacote da extensão amplia o secret scan.
- Sem auto-apply, inscrição, pagamento, envio de documentos ou scraping autenticado novo.
- Sem alteração no fluxo `authenticated-browser`.

## [1.9.5] - 2026-07-11

### Adicionado

- Identidade e deduplicação compartilhadas para Perfil, memória, oportunidades, projetos e editais.
- Trace de IA com provider/modelo solicitado e usado, prompt/versionamento, fallback e evidências.
- Sete personas multiárea coerentes e restauração segura da demo.
- Dashboard agregado, verificação de checkout limpo, roteiro e case study.
- Captura padronizada de screenshots/GIF do produto e extensão.

### Alterado

- Extensão atualizada para v0.9.1 com UI moderna, fila offline, análise independente local e providers Gemini/OpenAI próprios opcionais.
- Catálogos Gemini/OpenAI consultados nas APIs oficiais, com cache e seleção de modelo aplicada à chamada real.
- Enriquecimento público de perfis/repositórios GitHub com README, commits, estrutura, linguagens e atividade, sem autenticação.
- `source_ref` percorre Perfil -> Career Context -> APIs/UI.
- `pyproject.toml` passa a sustentar o comando documentado `pip install -e .[dev]`.
- Build PEP 517, verificador imune a `PIP_NO_BUILD_ISOLATION` externo e EOL LF portável.
- Settings remove implementação antiga não consumida; mocks e versões foram alinhados.

### Segurança

- Chaves próprias da extensão isoladas no service worker, em sessão por padrão e persistidas somente com consentimento; nunca em `chrome.sync` ou content script.
- Chave configurada no app continua exclusivamente no backend local e nunca é devolvida à extensão.
- Sem auto-apply, inscrição, pagamento, envio de documentos ou scraping autenticado novo.
- Sem alteração no `authenticated-browser`.

## [1.9.4] - 2026-07-07

### Adicionado

- Presets de IA em Configurações: Local seguro, IA básica, IA completa e Personalizado.
- Catálogo de modelos por provider com endpoints `/api/v1/settings/ai/providers`, `/models` e `/models/refresh`.
- Provider OpenAI no backend local, com secret separado, modelo selecionado, teste de conexão mockável e fallback local.
- Cache local de catálogo em `data/settings/ai-models-cache.json` e segredos locais ignorados por Git em `data/secrets/`.
- Testes opt-in `external_ai` para Gemini/OpenAI reais via `SOTUHIRE_TEST_GEMINI_API_KEY` e `SOTUHIRE_TEST_OPENAI_API_KEY`.
- Extensão com ação **Capturar edital / concurso**, tipo `public_exam`, endpoint local `/capture/public-exam` e contexto seguro `/capture/context-summary`.
- Importação de captura da extensão para `/public-exams?capture_id=...` como rascunho revisável.
- Documentação de catálogo de modelos, QA ponta a ponta e ponte segura da extensão.

### Alterado

- Gemini e OpenAI usam o modelo salvo no backend local nos fluxos estruturados.
- `openai_future` é normalizado para `openai` para compatibilidade com configurações antigas.
- Settings de IA deixam de exibir uma lista gigante por padrão e agrupam opções avançadas.
- Editais/Concursos retornam `requested_provider`, `provider_used` e `analysis_mode` com fallback local quando provider falha.
- Área de Fontes/Captura diferencia `public_exam` de vaga privada e permite importar como edital.
- A extensão consulta apenas resumo seguro do Perfil Universal; não recebe perfil inteiro, memória completa ou chave de IA.
- README, docs, MkDocs e roadmap atualizados para v1.9.4.

### Segurança

- API keys continuam restritas ao backend local/env local.
- Sem API key no frontend, `localStorage`, `sessionStorage`, extensão, docs, fixtures ou release notes.
- Sem inscrição automática, candidatura automática, pagamento, boleto ou envio automático de documentos.
- Sem login em banca/órgão, crawler logado, captura de cookies/tokens/sessão/headers ou bypass de CAPTCHA.
- Sem alteração no fluxo `/api/v1/sources/authenticated-browser/collect`.

## [1.9.3] - 2026-07-03

### Adicionado

- `modules/public_exams` com modelos, parser local, service, scoring, store, formatadores e plano de estudo inicial.
- Importação de edital por texto colado com extração local de órgão, banca, cargo, salário, taxa, datas, requisitos, etapas, documentos e conteúdo programático.
- Endpoints `/api/v1/public-exams` para importar draft, listar, consultar, confirmar, excluir, analisar e gerar plano de estudo.
- Prompt `public_exam_notice_extractor_v1` para estruturar editais com Gemini opcional como rascunho revisável.
- Tela `/public-exams` no frontend web com análise, warnings, cargos, timeline, requisitos, checklist, Exam Fit Score e plano inicial.
- Comparação inicial com o Perfil Profissional Universal, Career Context Engine `public_exams` e evidências acadêmicas/Lattes já confirmadas.
- Preparação de Radar/Tracker para tipos e status de oportunidades públicas sem misturar com candidatura privada.

### Alterado

- Health API anuncia `public_exams_foundation`.
- Radar passa a reconhecer `public_exam`, `academic_call`, `scholarship`, `residency` e `internship_public` como tipos separados.
- README, roadmap, mapa de integração, docs de concursos/editais, Prompt Registry e MkDocs documentam a fundação v1.9.3.
- Versão do projeto, API e frontend atualizada para `1.9.3`.

### Segurança

- Sem inscrição automática em concurso, edital, bolsa, residência, estágio público ou chamada pública.
- Sem pagamento automático, boleto automático ou envio automático de documentos.
- Sem login em banca/órgão, scraping autenticado, crawler logado ou bypass de CAPTCHA.
- Sem API key do app no frontend.
- IA não salva edital nem decide elegibilidade final sem revisão humana.
- O edital oficial sempre prevalece.
- Sem alteração no fluxo `/api/v1/sources/authenticated-browser/collect`.

## [1.9.2] - 2026-06-30

### Adicionado

- `modules/academic` com parser local de texto colado do Currículo Lattes.
- Endpoints `/api/v1/profile/import-lattes`, `/api/v1/profile/lattes/draft` e `/api/v1/profile/lattes/confirm`.
- Prompt `profile_lattes_extractor_v1` para extração acadêmica assistida por Gemini.
- Seção **Acadêmico / Lattes** na rota `/profile`.
- Evidências acadêmicas no Career Context Engine com purposes `academic`, `lattes` e `public_exams`.
- Fundação documental para editais e concursos.

### Alterado

- README e docs principais revisados com português, acentos e linguagem mais consistente.
- ATS, Tailor e GitHub/Portfólio passam a considerar evidências acadêmicas confirmadas no Perfil Profissional Universal.
- Roadmap, MkDocs, índice documental e catálogo de prompts documentam Lattes/acadêmico.
- Versão do projeto, API e frontend atualizada para `1.9.2`.

### Segurança

- Nada extraído do Lattes é salvo sem revisão humana.
- Gemini atua como extrator assistido, não como fonte de verdade.
- Sem login, scraping autenticado ou crawler do Lattes.
- Sem inscrição automática em concursos ou editais.
- Sem alteração no fluxo `/api/v1/sources/authenticated-browser/*`.

## [1.9.1] - 2026-06-30

### Adicionado

- `modules/context` com Career Context Engine para Perfil Universal, RAG local e sinais do produto.
- Formatadores de contexto para prompts locais/externos, evidências do Match Engine e candidatos de perfil vindos de GitHub/Portfólio.
- Integração inicial de contexto em Wishlist, Radar, Scheduler, Match, ATS, Tailor, Tracker, Fontes, Notificações e GitHub/Portfolio.
- Testes para engine, deduplicação, RAG local, privacidade, APIs de contexto e README.
- Script `scripts/capture_web_walkthrough.py` para screenshots/GIF do frontend web moderno.
- Documentação do Career Context Engine e release notes v1.9.1.

### Alterado

- README reestruturado como página profissional do projeto, sem seções internas presas a versões antigas.
- Screenshots e GIF principais agora usam nomes sem versão.
- `MemoryStore()` passa a respeitar `SOTUHIRE_DATA_DIR` por padrão.
- Roadmap, mapa de integração, índice documental e MkDocs atualizados para refletir contexto unificado.
- Versão do projeto, API e frontend atualizada para `1.9.1`.

### Corrigido

- Tag `v1.9.0` revisada no commit final da main com `package-lock.json` validado.
- Validação do lockfile do frontend confirmada com `npm ci`.

### Segurança

- Contexto sensível é omitido de payload externo.
- Dados de perfil/memória só vão para provider externo quando `allow_memory_context=true`.
- GitHub/Portfólio retorna candidatos de evidência para revisão, sem salvar automaticamente no Perfil.
- Nenhum fluxo de authenticated browser, Chromium/CDP, cookie, token, sessão, headers, CAPTCHA ou auto-apply foi alterado.

## [1.9.0] - 2026-06-29

### Adicionado

- Scheduler local do Radar com CRUD em `/api/v1/radar/schedules`.
- Execução manual `run now` por agendamento.
- Histórico local de runs agendadas em `/api/v1/radar/scheduled-runs`.
- Runtime local com `/api/v1/radar/scheduler/status`, `start` e `stop`.
- Quiet hours e cooldown contra notificações repetidas.
- Central local de notificações em `/api/v1/notifications`.
- Seção **Agendamentos** e painel de notificações na tela Radar.
- Uso opcional do Perfil Profissional Universal em agendamentos.
- Testes backend e E2E para agendamentos, notificações e regressão de storage.

### Alterado

- Health API anuncia capabilities de `scheduled_radar` e `local_notifications`.
- Radar passa a aceitar fonte `authenticated_assisted_capture` como lembrete agendável e revisável.
- README, roadmap e docs de desenvolvimento documentam v1.9.0.
- Versão do projeto, API e frontend atualizada para `1.9.0`.

### Segurança

- Agendamentos não fazem auto-apply, envio automático de currículo ou candidatura.
- Captura assistida autenticada agendada não coleta cookie, token, sessão, headers ou storage de terceiros.
- API key continua backend-side e nunca retorna ao frontend.

## [1.8.2] - 2026-06-29

### Adicionado

- Perfil Profissional Universal persistido localmente em `data/profile/profiles.json`.
- Nova tela `/profile` no frontend moderno.
- Endpoints `/api/v1/profile*` para consultar, editar, importar texto, deduplicar e montar contexto.
- Prompt `profile_items_extractor_v1` no Prompt Registry.
- Extração local multiárea para itens de perfil com revisão humana obrigatória.
- Filtro por tipo e edição inline de itens do perfil no frontend.
- Integração do perfil persistido com Wishlist/Radar quando `use_profile_context=true`.
- Integração inicial segura de `ProfileContext` em Match/Tailor e captura de fontes.
- Endpoint `POST /api/v1/sources/authenticated-captures` para captura assistida autenticada revisável.
- Testes backend e frontend para perfil, importação, fallback, dedupe, multiárea e captura assistida.

### Alterado

- `ProfileContextOrchestrator` agora usa o Perfil Profissional Universal persistido antes do store legado.
- Health API anuncia capabilities de Perfil Profissional Universal e captura assistida autenticada.
- README, roadmap, mapa de integração, catálogo de prompts, docs frontend e release notes documentam v1.8.2.
- Versão do projeto, API e frontend atualizada para `1.8.2`.

### Segurança

- Itens extraídos por IA nunca são confirmados automaticamente.
- API key continua backend-side e nunca retorna ao frontend.
- Dados do perfil só entram em provider externo quando `allow_memory_context=true`.
- Captura assistida rejeita metadata com cookie, token, sessão, headers ou segredos.
- Nenhum fluxo sensível de authenticated browser, Chromium/CDP, crawler logado, CAPTCHA ou auto-apply foi alterado.

## [1.8.1] - 2026-06-29

### Adicionado

- Endpoint `POST /api/v1/radar/wishlists/draft` para gerar rascunho de wishlist a partir de texto livre.
- Prompt `job_wishlist_builder_v1` no Prompt Registry.
- Fallback local multiárea para wishlist do Radar, sem assumir tecnologia, GitHub, CLT, diploma ou experiência formal.
- `ProfileContext` e `ProfileContextOrchestrator` como preparação para Perfil Profissional Universal.
- Seção **Criar wishlist com IA** na tela Radar.
- Toggles de IA para currículo, vaga, importações e Radar.
- CI com frontend `npm ci`, lint, typecheck, build, smoke E2E Chromium e empacotamento da extensão.

### Alterado

- Radar mostra erros de fonte no card e desabilita execução quando não há fonte ativa.
- Wishlist do Radar ganhou campos editáveis para domínio, senioridade, termos a evitar, ATS mínimo e notas.
- README, roadmap, mapa de integração, docs de Radar e Prompt Registry atualizados para v1.8.1.
- Versão do projeto, API e frontend atualizada para `1.8.1`.

### Segurança

- Wishlist gerada por IA/local nunca é salva automaticamente.
- API key continua backend-side e nunca retorna ao frontend.
- Scores finais continuam no backend/core.
- Nenhum fluxo sensível de authenticated browser, Chromium/CDP, crawler logado, cookie, token, sessão,
  CAPTCHA ou auto-apply foi alterado.

### Validação

- Testes backend cobrem draft local, exemplos multiárea, Gemini fake, fallback por JSON inválido,
  toggle `allow_radar=false`, ausência de segredo e não persistência automática.
- Playwright cobre geração de draft, preenchimento do formulário, edição antes de salvar e regressões
  de storage/branding existentes.

## [1.8.0] - 2026-06-27

### Adicionado

- Tela **Radar de Vagas** no frontend moderno.
- Modelos e store local para `JobWishlist`, `RadarSource`, `RadarRun`, `RadarResult` e `RadarAlert`.
- Endpoints `/api/v1/radar/*` para wishlists, fontes, rodadas, resultados, alertas e estatísticas.
- Suporte a RSS/Atom público com refresh manual e revisão antes de salvar.
- Estrutura de adapters para APIs oficiais documentadas.
- Alertas locais para oportunidades acima do score mínimo da wishlist.
- Ações para salvar resultados do Radar na Caixa de Entrada ou em Candidaturas.
- Prompt `job_radar_match_explanation_v1` para explicação opcional com IA.
- Testes backend e E2E para Radar, alertas, RSS fake e modo Demo/API Real.

### Alterado

- Diretório de Fontes marca RSS público como disponível via Radar manual.
- README, roadmap, mapa de integração e docs de fontes documentam Radar, feeds públicos e limites.
- Health API anuncia capability `job_radar`.

### Segurança

- Score final do Radar permanece no backend/core.
- IA opcional apenas explica evidências/lacunas e faz fallback local.
- Nenhuma API key é salva ou retornada pelo frontend.
- Nenhum fluxo sensível de authenticated browser, Chromium/CDP, login manual, cookie, token,
  CAPTCHA, crawler logado ou auto-apply foi alterado.

## [1.7.1] - 2026-06-26

### Corrigido

- Textos públicos com mojibake no Kanban e teste de regressão para sequências comuns de encoding.
- Separação visual entre Modo Demo e API Real na Caixa de Entrada.
- Empty state da API Real sem oportunidades, sem misturar dados fictícios silenciosamente.
- Textos do Kanban para estágio, filtro, rejeição, análise e criação de candidatura.

### Adicionado

- Upload real de CSV/JSON pelo navegador com preview e confirmação antes de importar.
- Fluxo visual de mescla de duplicatas preservando histórico, fonte, link e notas.
- Exportação da Caixa de Entrada em CSV e JSON.
- Diretório de Fontes em **Fontes e Captura** para fontes públicas, feeds, APIs oficiais, CSV/JSON
  recorrente e links manuais.
- Endpoint `POST /api/v1/sources/captures/{capture_id}/merge`.
- Endpoints `GET /api/v1/sources/directory` e `POST /api/v1/sources/export`.
- Prompt `source_import_enrichment_v1` e schema seguro para enriquecimento opcional de importações.

### Alterado

- Importadores aceitam `use_ai=true` e fazem fallback local se provider não estiver configurado ou
  falhar.
- Duplicatas exibem comparação entre item novo e item existente.
- Fontes públicas/feeds ficam preparadas como diretório seguro, sem crawler amplo ou automação de
  conta.
- Roadmap, docs de fontes e mapa de integração atualizados para v1.7.1.

### Segurança

- Nenhuma chave de IA é salva no frontend, no `localStorage` ou no `sessionStorage`.
- A API key nunca retorna ao frontend e não entra em mocks, docs, prints ou testes.
- Nenhum fluxo de authenticated browser, Chromium/CDP, login manual, CAPTCHA, cookie, token,
  crawler logado ou auto-apply foi alterado.

### Validação

- Testes backend direcionados cobrem upload lógico CSV/JSON, merge, export, diretório, fallback de IA
  e ausência de segredo.
- Playwright cobre upload CSV/JSON via browser, preview antes da importação, merge visual, export,
  diretório de fontes, empty state API Real e regressão contra mojibake público.

## [1.7.0] - 2026-06-26

### Adicionado

- Caixa de Entrada de Oportunidades em **Fontes e Captura**.
- Importadores locais por texto, link, CSV e JSON.
- Histórico persistente de capturas/importações em store local ignorado pelo Git.
- Modelos `JobSource`, `JobImport`, `CaptureRecord`, `OpportunityInboxItem`, `ImportBatch` e
  `DuplicateCandidate`.
- Endpoints `/api/v1/sources/imports*`, `/api/v1/sources/captures*`, `/api/v1/sources/dedupe` e
  `/api/v1/sources/stats`.
- Deduplicação local explicavel por URL normalizada, empresa+cargo+localidade e texto normalizado.
- Ações para importar oportunidade para Vaga, salvar em Candidaturas e preservar origem no tracker.
- Histórico da extensão/local companion com patch seguro de status local.
- Screenshots e GIF v1.7 padronizados para os fluxos de importação.
- Documento `docs/07-development/v1.7.0-public-sources-importers-capture-history.md`.

### Alterado

- Fontes e Captura virou fluxo pratico de intake: texto/link/CSV/JSON, filtros, busca, duplicatas e
  fontes públicas planejadas.
- Cards do tracker preservam contexto de origem ao salvar itens importados.
- README, docs de frontend, mapa de integração, visual preview e guia da extensão foram atualizados
  para v1.7.0.

### Segurança

- O importador de URL faz apenas leitura pública simples e orienta colar texto quando a página
  bloqueia acesso, exige login ou não traz conteúdo legível.
- Nenhum fluxo sensível de authenticated browser, Chromium/CDP, login manual, crawler logado,
  CAPTCHA ou auto-apply foi alterado.
- Nenhum dado real, API key ou segredo foi usado em mocks, testes, docs ou screenshots.

### Validação

- Testes backend cobrem importação texto/link/CSV/JSON, dedupe, stats, captura para Vaga e tracker.
- Playwright cobre Caixa de Entrada, importações fake, duplicata, Kanban com origem e ausencia de
  branding legado público.

## [1.6.0] - 2026-06-24

### Adicionado

- Cobertura E2E cross-browser para Chromium, Firefox e WebKit.
- QA responsivo para mobile `390x844`, tablet `768x1024` e desktop `1440x1000`.
- Kanban com drag-and-drop visual, atualização otimista e rollback quando a API falha.
- Histórico mais rico da Extensão Local em Fontes e Captura.
- Estados de IA/fallback mais claros para provider local, configurado, não configurado, timeout,
  limite/erro e chave invalida.
- Screenshots v1.6 e GIF walkthrough v1.6 com dimensões padronizadas.
- Documento `docs/07-development/v1.6.0-stability-cross-browser-kanban.md`.

### Alterado

- Status do Kanban no frontend alinhados aos enums reais do backend.
- Match, ATS, Tailor e GitHub agora mostram explicabilidade, evidências usadas e prioridade de
  melhoria.
- Launcher Windows detecta portas ocupadas e mostra processo/PID.
- README raiz, docs de frontend, scripts e visual preview atualizados para v1.6.0.

### Segurança

- A chave de IA continua backend-side e nunca retorna ao frontend.
- Nenhum fluxo de authenticated browser, Chromium/CDP, scraper autenticado, crawler logado ou
  auto-apply foi alterado.
- Screenshots e mocks usam apenas dados fictícios.

### Validação

- Playwright executado em Chromium, Firefox e WebKit.
- Testes backend cobrem metadados seguros da ponte da extensão.
- Responsividade validada sem overflow horizontal de página nas rotas principais.

## [1.5.1] - 2026-06-23

### Adicionado

- Auditoria de prontidão de produto v1.5.1 com status real por funcionalidade.
- Fluxo guiado web-first na Home e no Dashboard.
- Blocos de recomendações acionáveis em Compatibilidade, ATS, Ajuste de Currículo e GitHub.
- E2E expandido para demos, IA Settings, Fontes e Captura, Kanban e branding legado.
- Screenshots v1.5.1 padronizados em `1440x1000` por Playwright.
- GIF walkthrough v1.5.1 mais lento e legível.

### Alterado

- Badges e textos de Local/IA/Fallback padronizados nas telas de análise.
- Painel **Extensão Local** mostra status do companion, origem, data, tipo e ações por captura.
- Kanban mostra origem, score, última análise, notas e data nos cards/lista.
- README raiz, `apps/web/README.md`, `scripts/README.md`, visual preview e mapa de integração
  atualizados para v1.5.1.
- Versão do projeto, API e frontend atualizada para `1.5.1`.

### Segurança

- A chave de IA continua backend-side e nunca retorna ao frontend.
- Nenhum fluxo de authenticated browser, Chromium/CDP, scraper autenticado, crawler logado ou
  auto-apply foi alterado.
- Screenshots e mocks usam apenas dados fictícios.

### Validação

- Testes backend adicionais cobrem toggles de IA por área e importações fake da extensão.
- Playwright cobre fluxo guiado, demos, IA Settings, Sources, Kanban e capturas visuais.

## [1.5.0] - 2026-06-23

### Adicionado

- Roteamento backend-side de IA opcional por área para currículo, vaga, compatibilidade, ATS,
  Tailor e GitHub.
- Prompts `match_analysis_evidence_based_v1`, `ats_analysis_v1`, `resume_tailor_v1` e
  `career_advice_v1` no Prompt Registry programático.
- Badges de provider/fallback no frontend moderno.
- Ponte FastAPI `/api/v1/extension/*` para capturas locais da Local Companion API.
- Painel **Extensão Local** em **Fontes e Captura**.
- Flag `-WithCompanion` no launcher web-first.
- Auditoria de integração v1.5 e mapa de integração de módulos.
- Testes de roteamento de IA, fallback local e ponte da extensão.

### Alterado

- Launcher Windows consolidado em `scripts/windows/start-sotuhire.ps1`.
- Wrappers `scripts/windows/start-api.ps1` e `scripts/windows/start-web.ps1` removidos por serem
  apenas delegadores.
- Frontend mostra quando uma análise usou local, Gemini ou fallback local.
- Local Companion capture store respeita `SOTUHIRE_DATA_DIR` para testes isolados.
- Versão do projeto, API e frontend atualizada para `1.5.0`.

### Segurança

- A chave de IA continua armazenada apenas no backend local e nunca retorna ao frontend.
- Gemini falha com fallback local e warning, sem quebrar análises.
- Scores finais continuam no backend/core.
- Nenhum fluxo de authenticated browser, Chromium/CDP, scraper autenticado, crawler logado ou
  auto-apply foi alterado.

### Validação

- Testes backend adicionados para rota Gemini fake, fallback e bridge da extensão.
- Smoke/E2E frontend cobre o painel **Extensão Local**.

## [1.4.0] - 2026-06-22

### Adicionado

- Launcher web-first para Windows com `.\start-sotuhire.ps1`.
- Scripts `scripts/windows/start-sotuhire.ps1`, `start-api.ps1` e `start-web.ps1`.
- Documentação de scripts em `scripts/README.md`.
- Endpoints seguros de IA em `/api/v1/settings/ai`.
- Armazenamento backend-side local para metadados e segredo de provider.
- Integração real da tela **Configurações → IA e Providers** com a FastAPI local.
- Smoke/E2E com Playwright em `apps/web`.
- Documento `docs/07-development/v1.4.0-web-first-local-launcher.md`.

### Alterado

- Frontend moderno em `apps/web` documentado como experiência local principal.
- Streamlit documentado como modo legado/dev/local debug, sem remoção de `app.py`.
- Versão do projeto, API e frontend atualizada para `1.4.0`.
- README raiz, docs de frontend e arquitetura atualizados para o fluxo web-first.

### Segurança

- A chave de IA fica apenas no backend local, em `data/secrets/ai-provider.local.json`.
- A API nunca retorna a chave para o frontend.
- O frontend não salva chave em `localStorage` ou `sessionStorage`.
- `data/`, `.env.local`, `apps/web/.env.local` e logs locais do launcher são ignorados pelo Git.
- Nenhum fluxo de authenticated browser, Chromium/CDP, scraper autenticado, crawler logado ou
  auto-apply foi alterado.

### Validação

- Testes de API dedicados para `settings/ai`.
- OpenAPI validado para `/api/v1/settings/ai`, `/api/v1/settings/ai/status` e
  `/api/v1/settings/ai/test`.
- Frontend: `npm run build`, `npm run lint`, `npm run typecheck` e `npm run test:e2e`.

## [1.3.0] - 2026-06-22

### Adicionado

- Frontend moderno em `apps/web`, integrado diretamente no repositório sem substituir a raiz.
- Stack React, Vite, TypeScript, TanStack Router, TanStack Query, Tailwind CSS, Radix UI,
  Recharts e lucide-react.
- Modo Demo com dados fictícios e modo API Real consumindo `http://127.0.0.1:8787/api/v1`.
- Client HTTP preparado para o envelope `{ ok, data, warnings, request_id }` da FastAPI local.
- Telas de Home/Landing, Dashboard, Currículo, Vaga, Análise de Compatibilidade, Análise ATS,
  Ajuste de Currículo, Análise de GitHub, Candidaturas, Inteligência de Candidaturas, Fontes e
  Captura, Configurações e Privacidade.
- Página **Fontes e Captura** integrada ao menu e à rota `/sources`.
- UI de **IA e Providers** em Configurações, marcada como integração planejada com backend local.
- Screenshots v1.3 do frontend moderno e walkthrough GIF em `docs/assets/screenshots`.
- Documento de desenvolvimento `docs/07-development/v1.3.0-modern-web-frontend.md`.

### Alterado

- Versão do projeto e da API local atualizada para `1.3.0`.
- README raiz atualizado com preview do frontend moderno, comandos `apps/web`, modo Demo/API Real
  e limites de segurança.
- Docs de frontend atualizados para refletir que o app moderno existe em `apps/web`.
- Visual preview atualizado para screenshots v1.3.
- Linguagem pública do produto alinhada para Análise de Compatibilidade, Pontuação de
  compatibilidade, Aderência, Confiança e Risco.

### Segurança

- Nenhum segredo é colocado no frontend.
- API keys não são persistidas em `localStorage` ou `sessionStorage`.
- Scores reais continuam no backend/core; o frontend não move regra de negócio crítica.
- O navegador autenticado autorizado existente foi exposto no frontend; ele exige login manual,
  autorização explícita, não contorna CAPTCHA/checkpoint e não faz auto apply.
- Streamlit, FastAPI, docs e testes existentes permanecem preservados.

### Validação

- Frontend: `npm install`, `npm run build`, `npm run lint` e `npm run typecheck`.
- OpenAPI validado para `/api/v1/health`, `/api/v1/match/analyze`, `/api/v1/ats/analyze` e
  `/api/v1/resume/tailor`.
- Smoke visual com Playwright/Chrome local cobrindo as rotas principais e ações demo.

## [1.2.0] - 2026-06-22

### Adicionado

- FastAPI local em `apps/api`, com `create_app()`, OpenAPI e docs interativas.
- Endpoint `GET /api/v1/health`.
- Endpoints de analise `POST /api/v1/resume/extract`, `POST /api/v1/job/extract`,
  `POST /api/v1/match/analyze`, `POST /api/v1/ats/analyze`, `POST /api/v1/resume/tailor` e
  `POST /api/v1/github/repo/analyze`.
- Endpoints do tracker `GET/POST /api/v1/tracker/jobs` e
  `PATCH /api/v1/tracker/jobs/{id}`.
- Endpoints de Application Intelligence `GET /api/v1/tracker/metrics`,
  `GET /api/v1/tracker/requirements`, `GET /api/v1/tracker/funnel` e
  `GET /api/v1/tracker/sources`.
- DTOs Pydantic para requests/responses da API, com envelope `ok`, `data`, `warnings` e
  `request_id`.
- Configuração local por env: `SOTUHIRE_API_HOST`, `SOTUHIRE_API_PORT` e
  `SOTUHIRE_API_ALLOWED_ORIGINS`.
- Script `scripts/run_api.py` para subir a API local.
- Funcoes de Application Intelligence em `modules/tracker/dashboard.py`, incluindo ranking por
  status, ranking por source, missing requirements, critical gaps, funnel e source metrics.
- Testes dedicados para health, resume, job, match, ATS, Tailor, GitHub, tracker e Application
  Intelligence.

### Alterado

- Versão do projeto atualizada para `1.2.0`.
- `docs/08-frontend/api-contract.md` passou a documentar a API real implementada na v1.2.0.
- Documentação de arquitetura passou a diferenciar Frontend API Layer e Local Companion API.
- README raiz passou a documentar `python scripts/run_api.py`, OpenAPI e `/api/v1`.
- Dependências FastAPI/Uvicorn/HTTPX foram adicionadas em `docs/requirements/requirements.txt`.

### Segurança

- CORS e restrito por default, sem wildcard.
- Respostas de resume/job extraction removem `raw_text` por default.
- A API reutiliza regras do core e não move Match, ATS, Tailor, GitHub Analyzer ou métricas oficiais
  para o frontend.
- Tracker continua local-first e sem armazenar currículo bruto.
- GitHub Analyzer aceita `fallback_payload` com dados públicos/capturados sem expor tokens no
  frontend.

### Validação

- Precheck antes da implementação: `ruff check .`, `ruff format --check .`, `pytest`,
  `mkdocs build --strict`, `python -m compileall modules tests`, `pyright` e
  `node --check docs/javascripts/sotuhire-demo.js`.
- Testes focados da API e Application Intelligence: `13 passed`.

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

- Versão do projeto atualizada para `1.1.0`.
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
- importação páginada de candidaturas já realizadas, com lote local de até 500 itens;
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
- pacote validado e documentação de públicação para a Chrome Web Store.

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
- captura assistida da vaga ou públicação atualmente aberta pela pessoa usuária;
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
