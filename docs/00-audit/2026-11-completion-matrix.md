# Matriz de conclusão — auditoria de 2026-11

Estado de cada obrigação do prompt mestre (C01–C28) e dos adendos v3/v4, com a evidência que o
sustenta. Branch `fix/copilot-execution-integrity`; SHAs e números por checkpoint estão no
[ledger](2026-11-checkpoint-ledger.md). `DONE` só quando a evidência cobre o critério inteiro;
`PARTIAL` diz o que falta. CI remoto ainda não rodou nesta branch (orçamento: gate final), então
nada aqui é "verde no CI".

| ID | Obrigação | Estado | Evidência | Falta |
| --- | --- | --- | --- | --- |
| C01 | Auditoria independente sem fronteira fixa | PARTIAL | inventário do Engine (1.509 arquivos), grafo de imports a partir dos entrypoints, achados fora da lista (SH-NEW-001…016) | Radar, Lattes, GitHub/portfólio e fontes sem leitura semântica completa |
| C02 | Reproduzir/refutar os 20 SH-AUD | PARTIAL | [ledger de findings](2026-11-independent-assurance-audit.md): 18 com decisão | SH-AUD-018 e 019 `UNKNOWN` |
| C03 | SH-NEW e novos achados | DONE | SH-NEW-001…016 com estado, teste e commit | — |
| C04 | Código morto Python e TS/JS | PARTIAL | duas camadas removidas, prova por item ([triagem](2026-11-dead-dedupe-triage.md)) | TS/JS sem análise de exports mortos |
| C05 | Triar os 170 candidatos do Engine | DONE | 152 tabelas + 18 corpos + 36 não referenciados + 68 de complexidade, decisão por item | 10 `DEFER` nomeados |
| C06 | Remover legado com migração segura | PARTIAL | repositório genérico removido; Streamlit em extra; `LocalStore` mapeado ([autoridade](2026-11-data-authority-map.md)) | matriz de retirada de JSON/JSONL com backup/rollback não executada |
| C07 | Simplificar arquitetura | PARTIAL | dependências 51→28 pacotes, um manifesto, vocabulários com dono único, dispatcher em tabela (34→21) | ciclo `modules.ai` ↔ `matching` documentado, não desfeito |
| C08 | Domínio e integridade | PARTIAL | aprovação no ponto de efeito, undo condicional, aceite com prova de credencial, regra de confirmação única | Radar/Tracker sem auditoria de transições |
| C09 | Dados, backup, restore, offline | PARTIAL | rascunho local não sobrescreve servidor; mapa de autoridade | round-trip de backup/restore e migração v6→v8 não reexecutados neste ciclo |
| C10 | IA agent-led do próprio SotuHire | PARTIAL | `plan()` declarado como não interpretativo; catálogo de prompts só conta consumidores reais | conectar `plan(intent)` a um consumidor ou retirar a capacidade |
| C11 | Frontend: todas as rotas, a11y, i18n | PARTIAL | 25 rotas × 4 larguras × 2 temas + en-US: claro 0, escuro 28 → 0 nós axe por largura; sem estouro nem erro de console ([UX](2026-11-frontend-product-ux.md)) | leitor de tela (`NOT_RUN`), redesign das telas além do shell e do Cockpit |
| C12 | Extensão e Companion | PARTIAL | sender/URL do service worker; tabela de rotas autenticadas testada | Chrome real com o ZIP distribuído não executado |
| C13 | Segurança e supply chain | PARTIAL | checagem de segredos única, SBOM transitivo, pins de Actions conferidos, secret scan | DAST/SSRF não reexecutados neste ciclo |
| C14 | Gates reais e release | PARTIAL | uploads obrigatórios, SBOM verificado, instalação limpa | CI remoto no SHA final pendente |
| C15 | Dependabot | DONE | 10 integradas com validação, 1 adiada com motivo ([dependências](2026-11-dependency-review.md)) | fechar as PRs supersedidas após o merge |
| C16 | Pesquisa externa | PARTIAL | OWASP, Chrome, career-ops, Reactive Resume, docs da Anthropic | comparativo de UX com mais produtos |
| C17 | Melhorias de produto | PARTIAL | Perfil → Currículo Mestre sem redigitação; provider Claude | legitimidade de vaga, follow-up, JSON Resume import na UI |
| C18 | Derivanta Framework aplicado e corrigido | DONE | `7e1ecba`: consumo de aprovação, artefatos obrigatórios, controles só alcançados por testes | — |
| C19 | Derivanta Engine aplicado e auditado | DONE | MCP e CLI com as mesmas 218 impressões; `compare` entre clones; `35f9951` | regra de "teste de módulo inalcançável" avaliada e não criada |
| C20 | Assertiva 1.0 aplicada e auditada | DONE | `--execute`, `--mutate` antes/depois, 3 correções, suíte 1.346 passed em `fee2c44` | — |
| C21 | Dogfood bidirecional verdadeiro | DONE | ciclo A→E do CP-04 com reteste cruzado; o reteste pegou um defeito do próprio patch | — |
| C22 | Documentação vs runtime | PARTIAL | catálogo de prompts, `.env.example`, métricas de IA, requirements, docs de planejamento marcados | varredura completa de docs antigos |
| C23 | Continuidade, branches, PRs | PARTIAL | 4 repos com branches publicadas e SHA conferido | PRs não abertas (gate final) |
| C24 | Validação final | NOT_RUN | — | CI no SHA final, Firefox/WebKit, release decision |
| C25 | Descobertas fora do roadmap | DONE | primeiro uso do Resume Studio sem saída, modelo do Gemini gravado para todo provider, rascunho que vencia o servidor | — |
| C26 | Instalação e operação | PARTIAL | extras documentados, `.env.example` real, instalação padrão menor | `ensure_database` (SH-NEW-001) não medido |
| C27 | Mercado brasileiro multiárea | PARTIAL | detector de credenciais com 26 conselhos; fixtures de saúde e engenharia | avaliação multiárea do matching |
| C28 | Fechar correções das ferramentas | PARTIAL | branches publicadas, CHANGELOG e testes próprios | PRs nos repositórios donos |
| v3/v4 | UX premium com antes/depois | PARTIAL | CP-UX00 baseline e CP-UX01 com galeria antes/depois | CP-UX02…06 |
| UX-01 | Baseline pré-redesign reproduzível | DONE | `459ffa9`, 250 telas + 10 estados, manifesto com hashes | — |
| UX-02 | Identidade e design system | DONE | tokens híbridos, superfícies, marca, `Field`/`TextField`, `SectionCard`/`StatCard`/`ScoreRing` compartilhados, tela inicial e todas as rotas sobre os mesmos tokens; ADR 006 revisado; fallback de fonte com métricas medidas | — |
| UX-03 | Navegação por jornada desktop/tablet/mobile | DONE | registro único, barra lateral, barra mobile, E2E `journey-shell` | — |
| UX-04 | Busca e autocomplete reais | DONE | telas e dados sem acento, todas as palavras, ranking; evidência, portfólio, Perfil (sem sensíveis), candidaturas; tipos legíveis; resposta atrasada não substitui a atual | — |
| UX-05 | Motion e microinterações com reduced-motion | DONE | tokens de duração e curva; entrada de página, abertura de jornada, elevação no hover, estados pendentes e de salvamento; tudo desligado em `prefers-reduced-motion`; suítes E2E rodam com animação normal nos 3 navegadores, capturas com movimento reduzido | — |
| UX-06 | Perfil e Resume Studio | DONE | CP-UX02: composição nova, `Field`, versões de variante, fatos alterados reconciliados, E2E demo e API real, 0 nós axe | reimportação sem aviso (dados) |
| UX-07 | Radar, fontes, Tracker | PARTIAL | CP-UX03: painel do Radar, funil e cartões do Tracker, lista no celular, Fontes com navegação; 0 nós axe; jornada do Tracker contra a API real | comparação de vagas lado a lado |
| UX-08 | Lab, Copilot, aprovações, Configurações | PARTIAL | CP-UX04: Aprovações recompostas, Copilot alinhado ao Cockpit, demo com máquina de estados, destino do texto da IA, orientação × mudança no Lab; E2E de ciclo, erro e undo | recomposição completa do Lab; chamadas reais a providers (`BLOCKED_EXTERNAL_CREDENTIALS`) |
| UX-09 | Demais rotas e limpeza de estilos | PARTIAL | CP-UX05: tela inicial na identidade nova, utilitários órfãos removidos, `TextField` compartilhado; 400 telas sem violação | interface das telas de produto só em pt-BR |
| UX-10 | Tema escuro e en-US medidos | DONE | CP-UX05: 400 telas, claro/escuro × pt-BR/en-US × 4 larguras, 0 nós axe | tradução das telas de produto está em UX-09 |
| UX-11 | Fluxos com API real | PARTIAL | 3 jornadas em diretório sintético: pareamento/Cockpit/busca; Perfil → Mestre → autosave → JSON/PDF → reconciliação; Tracker → busca sem acento → status persistido (achou SH-NEW-032) | Radar e Application Lab contra a API real; escritas que montam literais na tela não verificadas uma a uma (o teste de contrato cobre as que usam objetos de domínio) |
| UX-12 | Desempenho e matriz de navegadores | DONE | Chromium 48/0, Firefox 47/0, WebKit 47/0; Web Vitals de produção medidos (`scripts/measure-vitals.mjs`): LCP ≤ 2,4 s com 4× CPU, CLS ≤ 0,073 (tela inicial 0,14 → 0,002), interação ≤ 80 ms exceto Tracker 240 ms com 4× CPU (registrado) | — |
| v3/v4 | Dados informados uma vez | PARTIAL | projeção Perfil → Mestre com revisão | edição de fato já projetado; retirada de `LocalStore` |
| v3/v4 | Haiku 5.5 | PARTIAL | adapter com `MOCK_PASS` | chamada real `BLOCKED_EXTERNAL_CREDENTIALS` |
| v3/v4 | Commit + push por checkpoint | DONE | SHA remoto conferido em cada checkpoint | — |
| v3/v4 | CHANGELOG e docs por checkpoint | DONE | `CHANGELOG_GATE`/`DOCS_GATE` no ledger | — |

**Conclusão honesta:** das 28 obrigações do prompt mestre, 8 estão `DONE`, 19 `PARTIAL` e 1 `NOT_RUN`. Os riscos P0/P1 encontrados foram resolvidos, mas a auditoria integral não está concluída; cada linha diz o que falta.
