# Fidelidade dos exports

O oracle é a árvore canônica habilitada. O teste exporta a mesma variante para JSON Resume,
PDF A4/Letter e DOCX, reabre os binários e normaliza o texto para comparar seções, ordem e fatos.

Critérios: magic bytes/MIME corretos; hash e tamanho presentes; texto selecionável no PDF;
DOCX reabre sem reparo; Unicode preservado; blocos desabilitados ausentes; no trace/segredo/path;
metadados sanitizados; quebra de página dentro do limite; download frontend byte a byte.

O objetivo é fidelidade semântica e ATS-safe. Diferenças inevitáveis de paginação entre PDF e
DOCX são aceitas quando não removem, duplicam ou reordenam conteúdo.
