# Renderização de currículo

PDF, DOCX, JSON Resume e preview são projeções da mesma árvore canônica. O renderer não
reinterpreta texto, cria fatos nem inclui entradas desabilitadas. `document_hash`, template e
tamanho de página participam do `dependency_hash`, permitindo detectar artefato stale.

## PDF

PyMuPDF gera um PDF real em memória, A4 ou Letter, com texto selecionável, margens estáveis,
headings e quebras previsíveis. Não depende de navegador, LibreOffice, rede ou impressora. O
retorno inclui MIME, bytes em base64, tamanho e SHA-256; metadados não contêm caminho local.

## DOCX

python-docx gera um Office Open XML real usando estilos, parágrafos e listas. Tabelas de layout,
macros, relacionamentos remotos e campos executáveis não são usados. O documento pode ser
reaberto pela própria biblioteca para conferir headings, ordem e conteúdo.

## Fidelidade

Testes com currículos fictícios verificam assinatura, reabertura, texto, ordem de seções,
habilitação, A4/Letter, caracteres Unicode, metadados, consistência semântica entre formatos
e ausência de trace/segredo. A fidelidade é semântica e ATS-safe; não promete reprodução
pixel a pixel de um documento importado.
