# Frontend: acessibilidade, continuidade de dados e evidência antes/depois — 2026-11

Parte da [auditoria de 2026-11](2026-11-independent-assurance-audit.md) (CP-FE00, CP-FE01a e, a partir
do adendo v5, o redesign CP-UX00…06). A seção [Redesign 2026-11 v5](#redesign-2026-11-v5) tem a baseline
nova e a galeria antes/depois do redesign; as seções anteriores são o registro histórico da correção
de acessibilidade e não provam o redesign.

## Método

`apps/web/tests/e2e/ux-baseline.spec.ts` (só com `CAPTURE_UX=1`) captura 22 rotas em 1440×900 e 390×844,
tema claro, `prefers-reduced-motion`, pt-BR, dados demo fictícios, Chromium. Para cada tela grava a
captura de página inteira e um registro com estouro horizontal, violações do axe-core 4.14 (regras
WCAG 2.0/2.1/2.2 A e AA) por impacto, com elementos e cores, e erros de console. O mesmo arquivo gera o
antes e o depois.

- Antes: `8b9e82a`. Depois: o commit deste checkpoint.
- Hash SHA-256 do conjunto de registros JSON antes+depois (fora do repositório):
  `87654ed8261ab6a99406c0697ee8d53a229de1a00c64b54b4585cee5df6d1c0a`.
- axe automatizado não é certificação WCAG; leitor de tela e teste com pessoas continuam pendentes.

## Resultado (22 rotas × 2 viewports)

| Medida | Antes | Depois |
| --- | --- | --- |
| Nós com violação crítica | 20 (12 `select-name`, 8 `label`) | 0 |
| Nós com violação séria | 309 (288 `color-contrast`, 21 `label-content-name-mismatch`) | 0 |
| Telas com estouro horizontal a 390 px | 0 | 0 |
| Telas com erro de console | 0 | 0 |

## Causas e correções

| Causa | Correção |
| --- | --- |
| As cores semânticas de preenchimento (`accent`, `success`, `warning`, `destructive`) eram usadas também como cor de texto, inclusive sobre o próprio tom a 15%: contraste de 1,8 a 3,3:1 | Tokens de texto `--*-strong` para claro e escuro, calculados em OKLCH com mistura em sRGB codificado (o modelo reproduz exatamente a medição do axe, `#5e6770` sobre `#08121f` = 3,26:1): ≥ 5,2:1 sobre cartão, fundo e tons de 15–20%. 199 usos migrados de `text-X` para `text-X-strong`; os preenchimentos continuam para fundo, borda e ícone. |
| Rótulos de seção da barra lateral a 40% de opacidade (3,26:1) | 65% (6,7:1) |
| Busca universal com `aria-label` diferente do texto visível (WCAG 2.5.3) | o nome acessível é o texto visível "Buscar"; atalho em `aria-keyshortcuts` |
| 10 campos sem nome acessível em Perfil, Radar, Configurações e Fontes; dois `<label>` visíveis não associados ao campo | `htmlFor`/`id` onde havia rótulo; `aria-label` com o propósito nos demais |
| Selos do Tracker com texto `chart-1` e rótulos a 70% de opacidade | texto em `foreground`, hierarquia por peso |

Fora da contagem: um botão de Configurações apareceu desativado durante a captura (estado transitório
"verificando").

## Continuidade de dados na interface

Ver o [mapa de autoridade](2026-11-data-authority-map.md). No Resume Studio: tela de primeiro uso em vez
de erro, criação do Currículo Mestre a partir do Perfil, painel de fatos novos do Perfil com escolha
explícita, e rascunho local que não sobrescreve conteúdo mais novo.

## Antes e depois

| Tela | Antes | Depois |
| --- | --- | --- |
| Cockpit, desktop | ![](../assets/ux-comparison/2026-11/dashboard/desktop-before.png) | ![](../assets/ux-comparison/2026-11/dashboard/desktop-after.png) |
| Tracker, desktop | ![](../assets/ux-comparison/2026-11/tracker/desktop-before.png) | ![](../assets/ux-comparison/2026-11/tracker/desktop-after.png) |
| Tracker, mobile | ![](../assets/ux-comparison/2026-11/tracker/mobile-before.png) | ![](../assets/ux-comparison/2026-11/tracker/mobile-after.png) |
| Configurações, desktop | ![](../assets/ux-comparison/2026-11/settings/desktop-before.png) | ![](../assets/ux-comparison/2026-11/settings/desktop-after.png) |
| Perfil, mobile | ![](../assets/ux-comparison/2026-11/profile/mobile-before.png) | ![](../assets/ux-comparison/2026-11/profile/mobile-after.png) |

As demais 34 capturas de cada lado ficam fora do repositório (hash acima).

## Decisões de stack nesta fase

| Peça | Decisão | Motivo |
| --- | --- | --- |
| React, TanStack Router/Query, Vite, Tailwind, Radix | KEEP | os problemas medidos eram de tokens, rótulos e fluxo de dados, não de framework |
| `@axe-core/playwright` 4.14.0 (MPL-2.0) | ADD, só dev | medida objetiva de acessibilidade; não vai para o pacote |
| Biblioteca de animação | NOT_ADDED | `tw-animate-css` e CSS bastam até haver uma interação que justifique; `prefers-reduced-motion` é respeitado na captura |
| zod 3 → 4 | DEFER | advisory alto ainda aberto (ver [dependências](2026-11-dependency-review.md)); migração exige formulários e resolvers testados |

## Próximo

Redesign visual (identidade, tipografia, densidade, navegação por jornada) em fatias verticais com o
mesmo antes/depois; componente `Field` para associar rótulo e campo de forma sistemática (48 rótulos
sem `htmlFor` não acusados pelo axe porque o campo tem outro nome); verificação com leitor de tela.

## Redesign 2026-11 v5

Direção, alternativas e plano: [design-direction-2026-11](../08-frontend/design-direction-2026-11.md).
Decisão de arquitetura: [ADR 006](../02-architecture/adrs/006-journey-navigation-and-editorial-design-system.md).

### Baseline (CP-UX00, app em `459ffa9`)

250 telas (25 rotas × 4 larguras × 2 temas em pt-BR, mais 2 larguras em en-US) e 10 estados
interativos. Gerar de novo:

```bash
cd apps/web
CAPTURE_UX=1 CAPTURE_UX_DIR=<pasta>/before CAPTURE_UX_VIEWPORTS=desktop,tablet,mobile,small   CAPTURE_UX_THEMES=light,dark npx playwright test tests/e2e/ux-baseline.spec.ts --project=chromium
CAPTURE_UX=1 CAPTURE_UX_DIR=<pasta>/before CAPTURE_UX_VIEWPORTS=desktop,mobile CAPTURE_UX_LOCALES=en-US   npx playwright test tests/e2e/ux-baseline.spec.ts --project=chromium
CAPTURE_UX=1 CAPTURE_UX_DIR=<pasta>/before npx playwright test tests/e2e/ux-states.spec.ts --project=chromium
python scripts/build_ux_gallery.py --before <pasta>/before --before-sha 459ffa9   --out docs/assets/ux-comparison/2026-11-v5
```

| Medida (baseline) | Claro | Escuro |
| --- | --- | --- |
| Nós axe sérios/críticos, por largura | 0 | 28 (`color-contrast`) |
| Telas com estouro horizontal | 0 | 0 |
| Telas com erro de console | 0 | 0 |
| Links de navegação sempre visíveis (desktop) | 23 em 7 grupos | — |
| Resultados da busca para "curriculo", "currículo", "vaga" | 0, 0, 0 | — |

Hash SHA-256 do conjunto de registros JSON da baseline:
`dcde97062ffbe1c095d4008e208cd8215025eb63db149ed11eda508c8fc6abe8`; o `manifest.json` da galeria
tem o hash de cada arquivo. Uma captura de `/portfolio` (mobile, en-US) foi refeita porque o
servidor de desenvolvimento recarregou durante a análise do axe.

### CP-UX01 — design system, shell por jornada e busca

Mesma matriz da baseline (250 telas + 10 estados), mesmo navegador e dados.

| Medida | Antes | Depois |
| --- | --- | --- |
| Nós axe sérios/críticos, claro (por largura, pt-BR e en-US) | 0 | 0 (1 nó transitório em `/application-lab`, botão desativado capturado no meio da troca de estado; 12 recapturas sem ele) |
| Nós axe sérios, escuro (por largura) | 28 | 0 |
| Telas com estouro horizontal / erro de console | 0 / 0 | 0 / 0 |
| Links de navegação sempre visíveis (desktop) | 23 em 7 grupos | 5 jornadas + a jornada atual aberta + 4 de Sistema |
| Busca: telas encontradas para "curriculo", "currículo", "vaga" | 0, 0, 0 | 4, 4, 3 |
| Cockpit com a API fora do ar | zeros como dados, carregando sem fim | falha dita, aviso com "Dados de exemplo" e "Gerenciar conexão" |
| Modo API Real contra a API de verdade | Cockpit nunca carregava (SH-NEW-020, SH-NEW-021) | pareia, carrega, busca (`real-api-shell.spec.ts`) |
| JS de produção (gzip) | 429,6 KB | 436,4 KB (+6,8) |
| CSS de produção (gzip) | 17,4 KB | 19,5 KB (+2,1) |
| Fontes carregadas numa página pt-BR/en-US | 0 (fontes do sistema) | 4 arquivos latin, 198 KB (Source Serif 4 opsz 122 KB) |

Hash SHA-256 do conjunto de registros JSON do depois:
`710fd1a7da57bbfb9e72d30cc495402d8a5f17c2cd06880f00129b844c2b9f6f`. LCP/CLS/INP não foram medidos
(servidor de desenvolvimento; medição de produção fica para o CP-UX06).

| Estado | Antes (`459ffa9`) | Depois (CP-UX01) | O que mudou |
| --- | --- | --- | --- |
| Cockpit, desktop | ![](../assets/ux-comparison/2026-11-v5/dashboard-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5/dashboard-desktop-after.webp) | Navegação por jornada, título em serifa, próximos passos em português com o destino certo, faixa de indicadores no lugar de 4 cartões iguais |
| Cockpit, escuro | ![](../assets/ux-comparison/2026-11-v5/dashboard-desktop-dark-before.webp) | ![](../assets/ux-comparison/2026-11-v5/dashboard-desktop-dark-after.webp) | Tema escuro próprio; 28 nós de contraste por largura → 0 |
| Cockpit, mobile | ![](../assets/ux-comparison/2026-11-v5/dashboard-mobile-before.webp) | ![](../assets/ux-comparison/2026-11-v5/dashboard-mobile-after.webp) | Título inteiro (antes "C…"), barra de jornadas embaixo |
| Cockpit, tablet | ![](../assets/ux-comparison/2026-11-v5/dashboard-tablet-before.webp) | ![](../assets/ux-comparison/2026-11-v5/dashboard-tablet-after.webp) | Barra lateral por jornada a partir de 1024 px |
| API local fora do ar | ![](../assets/ux-comparison/2026-11-v5/api-unreachable-before.webp) | ![](../assets/ux-comparison/2026-11-v5/api-unreachable-after.webp) | Antes: "Carregando…" e zeros como dados. Depois: aviso com saída e a falha dita em palavras |
| Busca por "currículo" | ![](../assets/ux-comparison/2026-11-v5/search-curriculo-before.webp) | ![](../assets/ux-comparison/2026-11-v5/search-curriculo-after.webp) | 0 → 4 telas, com o termo destacado, sem depender de acento |
| Navegação mobile aberta | ![](../assets/ux-comparison/2026-11-v5/navigation-mobile-before.webp) | ![](../assets/ux-comparison/2026-11-v5/navigation-mobile-after.webp) | Jornadas recolhidas com propósito, Sistema compacto, estado da conexão |
| Resume Studio, primeiro uso | ![](../assets/ux-comparison/2026-11-v5/resume-studio-first-use-before.webp) | ![](../assets/ux-comparison/2026-11-v5/resume-studio-first-use-after.webp) | Shell novo; composição da tela fica para o CP-UX02 |
| Perfil, desktop | ![](../assets/ux-comparison/2026-11-v5/profile-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5/profile-desktop-after.webp) | Só tokens e shell mudaram; composição no CP-UX02 |
| Radar, desktop | ![](../assets/ux-comparison/2026-11-v5/radar-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5/radar-desktop-after.webp) | Só tokens e shell; CP-UX03 |
| Tracker, desktop | ![](../assets/ux-comparison/2026-11-v5/tracker-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5/tracker-desktop-after.webp) | Só tokens e shell; CP-UX03 |
| Preparar candidatura, desktop | ![](../assets/ux-comparison/2026-11-v5/application-lab-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5/application-lab-desktop-after.webp) | Só tokens e shell; CP-UX04 |
| Aprovações, desktop | ![](../assets/ux-comparison/2026-11-v5/approvals-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5/approvals-desktop-after.webp) | Só tokens e shell; CP-UX04 |
| Configurações, mobile | ![](../assets/ux-comparison/2026-11-v5/settings-mobile-before.webp) | ![](../assets/ux-comparison/2026-11-v5/settings-mobile-after.webp) | Só tokens e shell; CP-UX04 |
| Primeira visita | ![](../assets/ux-comparison/2026-11-v5/first-visit-before.webp) | ![](../assets/ux-comparison/2026-11-v5/first-visit-after.webp) | Onboarding de 8 etapas mantido; reavaliar no CP-UX02 |

Outras telas estão no manifesto. Redesign só de cor e shell nas telas marcadas acima não é redesign completo dessas telas.

### CP-UX01B — correção visual: barra marinho, gradientes e superfícies

Baseline × CP-UX01B, mesma matriz (25 rotas × 4 larguras × claro/escuro em pt-BR, mais os estados),
mesmo navegador e dados. O CP-UX01 fica na tabela anterior para comparação. Análise dos dez
critérios em [direção de design](../08-frontend/design-direction-2026-11.md#correcao-de-rumo-cp-ux01b-adendo-v52).

| Medida | Baseline | CP-UX01 | CP-UX01B |
| --- | --- | --- | --- |
| Nós axe sérios, claro (por largura) | 0 | 0 | 0 |
| Nós axe sérios, escuro (por largura) | 28 | 0 | 0 |
| Estouro horizontal / erro de console | 0 / 0 | 0 / 0 | 0 / 0 |
| JS / CSS de produção, gzip -9, mesma máquina | — | 450,3 / 19,2 KB | 451,3 / 20,0 KB |

O valor de 436,4 KB registrado no CP-UX01 veio do relatório do Vite, outro método; a comparação acima
mede `739023c` e o CP-UX01B do mesmo jeito. A primeira captura completa do CP-UX01B teve 5 nós
`svg-img-alt` em `/intelligence` (só tablet): os setores da pizza do Recharts têm `role="img"` sem
nome, e aparecer ou não depende do momento da animação. Corrigido com `aria-label` por setor;
recaptura nas 8 combinações sem violações.

| Estado | Baseline (`459ffa9`) | CP-UX01B | O que mudou |
| --- | --- | --- | --- |
| Cockpit, desktop | ![](../assets/ux-comparison/2026-11-v5/dashboard-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux01b/dashboard-desktop-after.webp) | Barra marinho volta; hero com gradiente e anel de cobertura; indicadores com ícone e cor; passos traduzidos e destinos do CP-UX01 mantidos |
| Cockpit, escuro | ![](../assets/ux-comparison/2026-11-v5/dashboard-desktop-dark-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux01b/dashboard-desktop-dark-after.webp) | Três planos (barra, fundo, cartões); 0 nós de contraste |
| Cockpit, mobile | ![](../assets/ux-comparison/2026-11-v5/dashboard-mobile-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux01b/dashboard-mobile-after.webp) | Barra de jornadas marinho; anel ao lado do texto; botões no tamanho do conteúdo |
| Cockpit, tablet | ![](../assets/ux-comparison/2026-11-v5/dashboard-tablet-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux01b/dashboard-tablet-after.webp) | Mesmo arranjo do desktop a partir de 1024 px |
| Navegação mobile aberta | ![](../assets/ux-comparison/2026-11-v5/navigation-mobile-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux01b/navigation-mobile-after.webp) | Menu "Mais" com o mesmo trilho escuro |
| API local fora do ar | ![](../assets/ux-comparison/2026-11-v5/api-unreachable-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux01b/api-unreachable-after.webp) | Falha dita e saída, agora sobre a hierarquia nova |
| Perfil, desktop | ![](../assets/ux-comparison/2026-11-v5/profile-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux01b/profile-desktop-after.webp) | Só tokens e cartões compartilhados; composição no CP-UX02 |
| Radar, desktop | ![](../assets/ux-comparison/2026-11-v5/radar-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux01b/radar-desktop-after.webp) | Indicadores herdam o `StatCard` novo; composição no CP-UX03 |

### CP-UX02 — Perfil, Resume Studio e primeira visita

Mesma matriz (25 rotas × 4 larguras × claro/escuro, pt-BR, mais estados): **0** nós axe sérios, 0
estouro horizontal, 0 erro de console em todas as combinações. Hash do conjunto JSON:
`d37061a1d1ff0c5b4fb81cbcd6238e3c70bb6f1406a046d7e717a8048e8f8e90`. A espera da captura passou de 400
ms para 1 s depois do `networkidle` (SH-NEW-029); com 400 ms o Application Lab mostrava 5 nós em 8
combinações, com 1 s, 0 na última de 3 repetições.

| Estado | Baseline (`459ffa9`) | CP-UX02 | O que mudou |
| --- | --- | --- | --- |
| Perfil, desktop | ![](../assets/ux-comparison/2026-11-v5/profile-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux02/profile-desktop-after.webp) | Hero com nome, headline, áreas e % de fatos confirmados; abas Fatos / Identidade / Importar com link direto; fatos com tipo legível, origem e estado; remover pede confirmação |
| Perfil, escuro | ![](../assets/ux-comparison/2026-11-v5-ux02/profile-desktop-dark-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux02/profile-desktop-dark-after.webp) | Mesma composição no tema escuro; 0 nós de contraste |
| Perfil, mobile | ![](../assets/ux-comparison/2026-11-v5-ux02/profile-mobile-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux02/profile-mobile-after.webp) | Abas com rótulo curto, ações do hero empilhadas |
| Resume Studio, desktop | ![](../assets/ux-comparison/2026-11-v5/resume-studio-desktop-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux02/resume-studio-desktop-after.webp) | Cabeçalho da variante com vínculos, páginas e pendências; barra de ferramentas agrupada (PDF como ação principal); painel do Perfil com fatos novos e fatos alterados lado a lado; preview em papel |
| Resume Studio, mobile | ![](../assets/ux-comparison/2026-11-v5-ux02/resume-studio-mobile-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux02/resume-studio-mobile-after.webp) | Barra de ferramentas deixa de ser fixa no celular |
| Resume Studio, primeiro uso | ![](../assets/ux-comparison/2026-11-v5/resume-studio-first-use-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux02/resume-studio-first-use-after.webp) | Sem os ~7 s de "Abrindo…" antes do onboarding (SH-NEW-023) |
| Primeira visita | ![](../assets/ux-comparison/2026-11-v5/first-visit-before.webp) | ![](../assets/ux-comparison/2026-11-v5-ux02/first-visit-after.webp) | 8 etapas → 2: idioma, tema e princípios; depois os caminhos de início como links |

Contra a API real, em diretório sintético (`real-api-shell.spec.ts`, 2 jornadas, rodadas no código
final): o fato é criado pela interface, o Mestre é montado a partir do Perfil, o autosave grava, o JSON
Resume exportado contém o fato e o PDF começa com `%PDF-`; a edição posterior no Perfil aparece como
diferença e é aplicada no Mestre a pedido.

![Resume Studio contra a API real](../assets/ux-comparison/2026-11-v5-ux02/real-api-resume-studio-after.webp)
