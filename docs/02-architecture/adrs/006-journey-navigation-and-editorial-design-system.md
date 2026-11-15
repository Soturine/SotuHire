# ADR 006: navegação por jornada e design system editorial

- Estado: aceito (2026-11, CP-UX00)
- Contexto: [direção de design](../../08-frontend/design-direction-2026-11.md)

## Contexto

A interface tinha três listas de telas independentes: o menu lateral (`app-shell.tsx`), a busca
(`command-palette.tsx`, com 4 telas em inglês) e o metadado de rotas (`route-metadata.ts`, usado pela
ajuda). Uma tela nova precisava entrar nas três, e a busca já tinha ficado para trás. A navegação era
agrupada por módulo técnico, e o visual era o de um painel SaaS genérico.

## Decisão

1. `src/lib/navigation.ts` é o único registro de telas navegáveis, agrupadas por jornada (Hoje, Quem
   eu sou, Currículos, Oportunidades, Candidaturas, Sistema). Menu, barra mobile, cabeçalho e busca
   leem dele. Rotas e endereços não mudam.
2. Busca sem acento e com ranking explicável em `src/lib/search.ts`, usada pela paleta e pela ajuda.
3. Tokens de cor, tipografia e motion em `styles.css`, com variantes `-strong` para texto sobre
   superfícies nos dois temas.
4. Fontes OFL auto-hospedadas via `@fontsource` (Source Serif 4, IBM Plex Sans, IBM Plex Mono),
   versões exatas: o app continua local-first e funciona offline; nenhuma requisição a CDN de fontes.

## Alternativas

- Biblioteca de animação (Motion for React): não adicionada. CSS e `tw-animate-css` cobrem entrada,
  saída e abertura de grupo; reavaliar só se uma interação precisar de layout compartilhado ou gesto.
- Fontes do sistema: sem custo de bundle, mas sem identidade e com métricas diferentes por sistema
  operacional, o que muda quebras de linha entre máquinas.

## Consequências

- Cada fonte custa um arquivo `woff2` por faixa Unicode usada (latin e latin-ext); medido no
  CP-UX01.
- Testes: `search.test.ts` exige que toda tela do registro seja encontrável pelo próprio rótulo.
