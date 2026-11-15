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
