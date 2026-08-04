# Resume Studio

O Resume Studio v1.9.9 em `/resume-studio` ingere PDF, DOCX, HTML, TXT e JSON Resume,
permite revisar os blocos e adotar uma árvore canônica como Currículo Mestre. Variantes
derivadas nunca removem nem sobrescrevem conteúdo do mestre.

## Modelo

- `MasterResume`, `ResumeSection` e `ResumeEntry` preservam ordem, ativação, confirmação e `source_refs`;
- `ResumeVariant` aponta para `master_resume_id` e, quando aplicável, `job_snapshot_id`;
- `ResumeVariantChange` registra antes, depois, motivo, evidência, warning e tipo;
- `ResumeTemplate` oferece clássico, compacto, técnico e acadêmico, todos ATS-safe;
- `ResumeExport` registra formato, estado, hash, MIME, page size e warnings;
- `DocumentProvenance` liga cada bloco à fonte, hash, método e página/localização.

O editor React implementa texto, ativação, reordenação, preview, A4/Letter, estimativa de páginas, debounce/autosave local e via API, undo/redo, diff e validação. A API pagina variantes e persiste mestre, variantes e exports em SQLite.

## Ingestão e export

O upload passa por limites de tamanho/páginas/ZIP, detecção de assinatura, sanitização
HTML e rejeição de PDF criptografado. O review diferencia `sourced`, `confirmed`, `rejected`
e `stale`; PDF somente-imagem pede revisão porque OCR automático não faz parte do fluxo.

JSON Resume inclui somente entradas habilitadas e permitidas. PDF real é renderizado com
PyMuPDF; DOCX real, com python-docx. Ambos são baixados pelo frontend como bytes, em A4 ou
Letter, e compartilham a mesma árvore do preview e do JSON. Nenhum formato inclui trace,
segredo ou caminho local.

## Proveniência

Variantes guardam `source_profile_item_ids` e change set. Ao salvar uma sessão no Tracker, mestre e variante recebem snapshots distintos; isso permite saber exatamente qual currículo foi usado sem congelar o Perfil editável.

Veja [ingestão e proveniência](document-ingestion-and-provenance.md),
[renderização](resume-document-rendering.md), [variantes e sugestões](../03-business-rules/resume-variants-and-suggestions.md)
e [testes de fidelidade](../09-testing/export-fidelity.md).
