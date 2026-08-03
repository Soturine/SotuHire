# Documento canônico, ingestão e exports

O Resume Studio mantém um `CanonicalProfessionalDocument` como fronteira de conteúdo. Editor,
preview textual, snapshots, JSON Resume, DOCX e PDF recebem a mesma estrutura habilitada; cada
representação expõe um SHA-256 verificável. Currículo Mestre e variante permanecem documentos
distintos: o snapshot informa `document_kind`, `master_resume_id` e `resume_variant_id` sem usar o
ID do mestre como se fosse uma variante.

## Ingestão local

O endpoint autenticado `POST /api/v1/resume-studio/ingest` aceita conteúdo base64 de PDF, DOCX,
HTML, TXT e JSON Resume. O pipeline:

- limita o arquivo a 10 MiB, o texto a 2 milhões de caracteres e PDF a 200 páginas;
- valida assinatura PDF/DOCX e rejeita extensão incompatível, caminhos e binários desconhecidos;
- rejeita PDF criptografado e contêiner DOCX com volume ou razão de compressão inseguros;
- nunca acessa rede e apenas avisa/ignora relacionamentos externos do DOCX;
- remove script, iframe, objeto, embed, estilos e handlers ativos do HTML;
- valida JSON Resume semanticamente, preservando o objeto estruturado;
- registra hash, método e localização por página em SQLite;
- classifica cada fato importado como `sourced`, nunca `confirmed`.

PDF baseado somente em imagem retorna `needs_review` e o aviso explícito de que OCR não foi
executado. Não há interpretação silenciosa nem fallback para documento vazio.

## Exports

DOCX é gerado por `python-docx` com headings e parágrafos sem tabelas de layout. PDF é gerado por
PyMuPDF, em A4 ou Letter, sem LibreOffice, navegador, rede ou dependência de sistema operacional.
O endpoint devolve o binário em base64 com MIME, tamanho, page size e hash canônico; JSON Resume
permanece objeto JSON interoperável e inclui metadados de evidência SotuHire.
