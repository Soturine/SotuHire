# Resume Studio

O Resume Studio em `/resume-studio` mantém um Currículo Mestre e variantes derivadas. O mestre é a fonte estável; remover, reordenar ou editar conteúdo em uma variante nunca remove o item original.

## Modelo

- `MasterResume`, `ResumeSection` e `ResumeEntry` preservam ordem, ativação, confirmação e `source_refs`;
- `ResumeVariant` aponta para `master_resume_id` e, quando aplicável, `job_snapshot_id`;
- `ResumeVariantChange` registra antes, depois, motivo, evidência, warning e tipo;
- `ResumeTemplate` oferece clássico, compacto, técnico e acadêmico, todos ATS-safe;
- `ResumeExport` registra formato, estado, hash e warnings.

O editor React implementa texto, ativação, reordenação, preview, A4/Letter, estimativa de páginas, debounce/autosave local e via API, undo/redo, diff e validação. A API pagina variantes e persiste mestre, variantes e exports em SQLite.

## Export

JSON Resume é funcional e inclui somente entradas habilitadas e confirmadas. O export não inclui trace interno. PDF e DOCX retornam estado `pending` e warning explícito: os renderizadores maduros e sua validação visual são pendência da v1.9.9. O preview para impressão já está disponível, mas não é apresentado como arquivo final.

## Proveniência

Variantes guardam `source_profile_item_ids` e change set. Ao salvar uma sessão no Tracker, mestre e variante recebem snapshots distintos; isso permite saber exatamente qual currículo foi usado sem congelar o Perfil editável.

Veja [variantes e sugestões](../03-business-rules/resume-variants-and-suggestions.md) e [testes do Studio](../09-testing/resume-studio-testing.md).
