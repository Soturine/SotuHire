# Direção de design 2026-11: dossiê de carreira

Documento vivo do redesign (adendo v5). Registra o estado medido antes, as direções consideradas, a
escolhida e o que cada checkpoint entrega. Evidência e números ficam na
[galeria](../00-audit/2026-11-frontend-product-ux.md#redesign-2026-11-v5) e no
[ledger](../00-audit/2026-11-checkpoint-ledger.md).

## Baseline pré-redesign (CP-UX00)

SHA do app: `459ffa9` (mesma interface de `f55b1d4`; o CP-SEC02 só mudou o tratamento de erro 409 de
um painel). Captura: 25 rotas reais (o spec anterior cobria 22; faltavam `/interviews`,
`/ai-quality` e `/help`) × desktop 1440×900, tablet 1024×768, mobile 390×844, pequeno 360×800 ×
claro/escuro em pt-BR, mais desktop e mobile em en-US: 250 telas, e 10 estados interativos. Chromium,
dados demo fictícios, `prefers-reduced-motion`. Imagens selecionadas e checksums de todas em
[`docs/assets/ux-comparison/2026-11-v5/`](../assets/ux-comparison/2026-11-v5/manifest.json).

O que a captura mostrou, além do axe:

| Área | Observado | Por que importa |
| --- | --- | --- |
| Navegação | 23 links sempre visíveis em 7 grupos por módulo ("Integrações", "Inteligência" ao lado de "Tracker"); no mobile, a mesma lista inteira num drawer | o caminho Perfil → Currículo → Vaga → Candidatura não aparece; tudo tem o mesmo peso |
| Busca (Ctrl+K) | só 4 telas, com nomes em inglês mesmo em pt-BR; "curriculo", "currículo" e "vaga" retornam **0 resultados** | a busca não leva às telas mais usadas |
| API local fora do ar | Cockpit fica em "Carregando estado da carreira…" sem fim e mostra 0%, 0, 0, 0 como se fossem dados | um zero falso parece um fato sobre a carreira da pessoa |
| Cabeçalho mobile | título truncado em "C…" atrás de 5 botões de ícone | a pessoa não sabe em que tela está |
| Identidade | barra lateral azul-marinho com ícone "Sparkles", 4 cartões de KPI idênticos, tipografia do sistema | é o visual de um painel SaaS genérico |
| Texto | ações do Cockpit em inglês e caixa alta ("INTERVIEW PREP DUE", "high") dentro da interface pt-BR | mistura de idiomas e de registro |
| Tema escuro | **28 nós sérios de contraste por viewport**, nunca medidos antes (o 0/0 anterior era só tema claro). Causa: `text-*-foreground` (texto para cor cheia) usado sobre tons de 10–15% | o escuro é uma opção oferecida no onboarding |
| Primeira visita | 8 etapas de onboarding antes de qualquer tela | — mantido para avaliação no CP-UX02 |

Tema claro: 0 violações axe nas 4 larguras e em en-US; nenhuma tela com estouro horizontal ou erro
de console.

## Direções consideradas

| Direção | Ideia | Prós | Contras e riscos |
| --- | --- | --- | --- |
| A. **Dossiê de carreira** (escolhida) | papel e tinta: superfícies claras e quentes, títulos em serifa, dados em monoespaçada, marcações de evidência como num documento revisado | combina com o que o produto faz (fatos confirmados, origem, revisão); distingue do SaaS genérico; densidade boa para leitura | serifa mal usada parece "blog"; exige disciplina para manter as telas analíticas densas |
| B. Console de instrumentos | fundo escuro, grade técnica, monoespaçada predominante | forte para diagnóstico e dados | frio para quem não é técnico (o produto é multiárea: saúde, direito, engenharia); repete o clichê "dev tool" |
| C. Manter o atual e polir | mesma barra marinho, cartões, sombras | menor risco | é exatamente o "painel SaaS qualquer" que o adendo rejeita |

## A direção escolhida

- **Paleta**: papel `oklch(0.975 0.008 85)`, tinta `oklch(0.21 0.025 265)`, verde-pinho para
  evidência confirmada, ocre "marca-texto" para o que está pendente de revisão, vermelho-selo para o
  que espera a pessoa. Cada cor de texto tem variante `-strong` com contraste calculado nos dois
  temas; cor nunca é o único sinal (ícone e palavra acompanham).
- **Tipografia** (fontes OFL empacotadas, funcionam offline): Source Serif 4 para títulos de página
  e números de destaque; IBM Plex Sans para interface; IBM Plex Mono para rótulos de seção, dados
  técnicos e números tabulares.
- **Marca**: monograma próprio (uma trajetória que liga dois pontos dentro de um selo), no lugar do
  ícone genérico; favicon SVG.
- **Navegação por jornada**: Hoje · Quem eu sou · Currículos · Oportunidades · Candidaturas, e
  Sistema. No desktop, a jornada atual fica aberta e as outras recolhidas com uma linha de propósito.
  No mobile, barra inferior com as 5 jornadas e "Mais". Toda tela continua com o mesmo endereço.
- **Cabeçalho de página**: jornada como sobrelinha, título em serifa, descrição e ações; no mobile,
  título inteiro e ações secundárias num menu.
- **Busca**: uma só paleta (`cmdk`) com todas as telas do registro, sem acento, com ranking
  explicável, destaque seguro, visitados recentemente, dados locais com debounce e estados de
  carregamento, falha e modo de exemplo.
- **Motion**: tokens de duração e curva; entrada de página e abertura de grupo com opacidade e
  translação curta; tudo desligado com `prefers-reduced-motion`.
- **Estado da API**: o modo e a conexão aparecem como um fato com explicação e saída, não como um
  selo; telas não mostram zeros quando a API falhou.

## Checkpoints

| CP | Entrega |
| --- | --- |
| CP-UX00 | baseline acima, specs de captura e estados, galeria "antes", esta decisão |
| CP-UX01 | tokens claro/escuro, fontes, marca, shell com jornadas (desktop, tablet, mobile), cabeçalho, estado da API, busca unificada; correção do contraste no escuro |
| CP-UX02 | Perfil e Resume Studio |
| CP-UX03 | Radar, fontes, Tracker; jornada vaga → análise → acompanhamento |
| CP-UX04 | Application Lab, Copilot, aprovações, Configurações |
| CP-UX05 | demais rotas e limpeza de estilos sem consumidor |
| CP-UX06 | galeria final, matriz de navegadores, a11y nos dois temas e idiomas, desempenho |

## Entregue no CP-UX01

- Tokens claro/escuro em `apps/web/src/styles.css` (papel, tinta, pinho, ocre, selo, variantes
  `-strong`, durações e curvas de motion); utilitários `eyebrow`, `tabular` e `mark-pending`.
- `src/lib/navigation.ts` (registro único de telas por jornada), `src/lib/search.ts` (busca sem
  acento com ranking e destaque seguro), `src/components/brand.tsx` e `public/favicon.svg`.
- Shell (`app-shell.tsx`): jornada atual aberta com linha de propósito; grupo Sistema compacto;
  estado da conexão no rodapé da barra; aviso global quando a API cai, com saída; link "pular para
  o conteúdo"; barra de jornadas no celular com rótulos curtos; animação de entrada de página
  desligada por `prefers-reduced-motion`.
- Busca (`command-palette.tsx`): uma instância para o app, aberta por Ctrl+K ou pelos botões;
  seleção acompanha o melhor resultado ao digitar.
- Estados compartilhados (`states.tsx`) e Cockpit refeitos com os componentes novos.
- Primitivos shadcn: hover e foco de botões e menus em `secondary`, não no verde da marca.

Fica para os próximos checkpoints: as demais telas ainda usam cartões e espaçamentos antigos sobre
os tokens novos (a mudança de cor e fonte chega a todas, a de composição só ao Cockpit e ao shell).

## Correção de rumo (CP-UX01B, adendo v5.2)

A revisão das capturas do CP-UX01 lado a lado com a baseline mostrou que a direção "dossiê" acertou a
estrutura e errou a superfície: papel bege na barra e no conteúdo, quase sem cor, tudo no mesmo
plano. O adendo v5.2 pediu uma terceira versão que juntasse o melhor das duas.

| Critério | Baseline `459ffa9` | CP-UX01 `739023c` | Veredito | CP-UX01B |
| --- | --- | --- | --- | --- |
| Identidade e marca | ícone "Sparkles" genérico, mas barra marinho memorável | monograma próprio; resto anônimo | marca melhorou, presença piorou | monograma em selo petróleo→azul sobre a barra marinho; favicon e `theme-color` iguais |
| Navegação × conteúdo | contraste forte (marinho × branco) | barra bege sobre fundo bege | **piorou** | barra marinho nos dois temas (no escuro, mais escura que o fundo e com borda própria); barra de jornadas do celular também |
| Cor e gradientes | gradiente teal no hero, verde-água vivo | pinho apagado, sem gradiente | **piorou** | gradiente marinho→petróleo só no hero; gradiente de marca no primeiro passo; lavagem petróleo nas forças comprovadas |
| Profundidade | cartões brancos com sombra sobre cinza-azulado | quase tudo plano, só borda | **piorou** | hierarquia `canvas` < `surface-muted` < `surface` < `surface-raised`, sombras suaves e elevação no hover |
| Hierarquia tipográfica | sans em tudo, títulos fortes | serifa em títulos e números | números em serifa ficaram "relatório" | serifa só no título da página e na frase do hero; números em Plex Sans tabular (`text-metric`) |
| Densidade | 4 cartões grandes iguais | faixa compacta de indicadores | melhorou | 4 indicadores com ícone e cor próprios, mais baixos que os da baseline |
| Legibilidade e varredura | ações em inglês e caixa alta | ações em português, destinos certos | **melhorou**, mantido | mantido; primeiro passo como botão principal, os demais secundários |
| Cartões, formulários, indicadores | genéricos | linhas finas, pouco contraste de controle | igual | `StatCard`, `SectionCard` e `ScoreRing` compartilhados atualizados (as telas que usam herdam) |
| Tema escuro | 28 nós de contraste por largura | 0 nós, mas plano | contraste melhorou, separação não | 0 nós; barra, fundo e cartões em três níveis distintos |
| Desktop, tablet, mobile | título truncado no celular | título inteiro, barra de jornadas | **melhorou**, mantido | mantido; botões do Cockpit no celular deixam de ocupar a largura toda |

Decisões:

- A barra lateral é uma "ilha escura": `class="dark"` no `<aside>`, no menu "Mais" e na barra do
  celular. Selo de API, busca, foco e qualquer componente compartilhado lá dentro usam os tokens do
  tema escuro sem cor fixa no componente. Os tokens `--sidebar-*` ficam em `:root` e `:root.dark`
  (seguem o tema da página, não a ilha).
- Gradiente tem lugar marcado: o hero (`.trajectory-surface`, uma afirmação por tela), o primeiro passo
  e o anel de cobertura. Cartões comuns não recebem gradiente.
- Ocre "marca-texto" e vermelho-selo continuam com o mesmo papel semântico (revisão pendente;
  espera a pessoa).
- A serifa fica: dá identidade aos títulos sem custo novo (já estava no bundle). Deixou os números.

Não mudou: navegação por jornada, busca, estados de erro e vazio, traduções, destinos das ações,
avisos de modo de exemplo e API Real.

## Entregue no CP-UX02

- **Perfil**: o hero (a "afirmação" da tela) mostra quem é a pessoa e quanto do que está registrado ela
  confirmou. O resto vira três abas com endereço próprio, para não empilhar seis formulários: fatos
  (o que alimenta tudo), identidade e objetivos (o que se edita raramente) e importação (o que se usa
  uma vez). Fatos pendentes têm marca ocre e uma ação "Confirmar"; remover pede confirmação.
- **Resume Studio**: o cabeçalho da variante responde "o que estou editando, de onde veio e o que
  falta"; a barra de ferramentas separa modo, histórico e saída; o estado de salvamento é anunciado
  (`role=status`) e o conflito com outra aba é um alerta com duas saídas, nunca uma gravação por cima.
- **`Field`** (`src/components/field.tsx`): rótulo ligado ao controle, "opcional" como texto real,
  dica e erro em `aria-describedby`, estilos únicos de controle (`controlClass`, `textareaClass`).
  Aplicado no Perfil e no Resume Studio; as demais telas migram nos próximos checkpoints.
- **Primeira visita**: 2 etapas. A primeira define idioma e tema e diz as três regras do produto; a
  segunda oferece os caminhos como links. Os textos das 8 etapas antigas foram mantidos, só agrupados.
