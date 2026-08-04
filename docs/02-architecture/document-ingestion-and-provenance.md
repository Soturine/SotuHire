# Ingestão documental e proveniência

`POST /api/v1/resume-studio/ingest` recebe base64 apenas em uma sessão local autenticada.
O pipeline identifica o tipo pelo conteúdo, aplica limites antes da extração e produz uma
`CanonicalProfessionalDocument`. Extensão incompatível com assinatura, PDF criptografado,
ZIP/DOCX suspeito, HTML ativo ou payload acima dos limites falham explicitamente.

| Formato | Extração | Proteção específica |
|---|---|---|
| PDF | PyMuPDF, por página/bloco | máximo de páginas; documento somente-imagem vira `needs_review`; sem OCR silencioso |
| DOCX | python-docx, parágrafos/tabelas | assinatura ZIP, total descompactado, razão de compressão e relacionamentos externos ignorados |
| HTML | parser stdlib | scripts, iframes, objetos, embeds, estilos e handlers removidos; sem rede |
| TXT | UTF-8/decodificação segura | limite de caracteres e rejeição de conteúdo binário |
| JSON Resume | schema semântico | objeto original validado; extensões SotuHire preservam lineage |

Cada bloco mantém `source_hash`, tipo, método de extração, localização/página, avisos e
`source_refs`. A origem prova de onde o texto veio; não prova que ele foi revisado. Por isso,
conteúdo importado entra como `sourced`, pode ser aceito/rejeitado/editado e só então compor
o Currículo Mestre confirmado. O binário bruto não é copiado para IA externa nem para a extensão.

A árvore canônica alimenta editor, diff, preview, hashes, snapshots e todos os exports.
Detalhes de rendering estão em [renderização de documentos](resume-document-rendering.md).
