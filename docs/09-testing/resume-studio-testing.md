# Testes do Resume Studio

Os testes Python validam mestre, seções, entries, variantes, changes, templates, round-trip JSON Resume e exports reais PDF/DOCX. A API cobre persistência, paginação, atualização e export.

Vitest cobre reducer do editor: edição, reorder, ativação, undo/redo e estimativa de páginas. Playwright valida autosave visível, preview, diff e downloads; testes Python reabrem PDF/DOCX e conferem conteúdo, metadados seguros e semântica.

PDF/DOCX são entregas vigentes desde a v1.9.9. O gate mantém seleção de texto, A4/Letter, quebras previsíveis e fidelidade sem prometer layout idêntico ao documento importado.
