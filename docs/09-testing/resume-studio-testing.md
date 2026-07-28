# Testes do Resume Studio

Os testes Python validam mestre, seções, entries, variantes, changes, templates, JSON Resume e estados pendentes de PDF/DOCX. A API cobre persistência, paginação, atualização e export.

Vitest cobre reducer do editor: edição, reorder, ativação, undo/redo e estimativa de páginas. Playwright valida autosave visível, preview, diff, download JSON e warning honesto de PDF.

O aceite não considera PDF/DOCX prontos. Para a v1.9.9 serão necessários renderer, metadados seguros, A4/Letter, seleção de texto, quebras previsíveis e regressão visual dos arquivos finais.
