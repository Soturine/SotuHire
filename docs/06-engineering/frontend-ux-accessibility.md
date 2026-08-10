# Frontend, UX e acessibilidade

Gate de desenvolvimento: 390/768/1440 px, zoom 200%, teclado, foco visível, labels, landmarks, heading order, contraste nos dois temas e `prefers-reduced-motion`.

Modais/drawers novos usam Radix para trap de foco e Esc. `SectionCard` começa em h2. Query keys que dependem de API incluem `mode` e `baseUrl`. O menu móvel usa Sheet; ajuda e preferências permanecem acessíveis no cabeçalho.

`test:e2e` é Chromium; `test:e2e:cross-browser` cobre Chromium, Firefox e WebKit. O gate completo roda somente após freeze.
