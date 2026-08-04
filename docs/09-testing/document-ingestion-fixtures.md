# Fixtures de ingestão documental

As fixtures são totalmente fictícias e cobrem TXT/HTML/PDF/DOCX/JSON Resume, Unicode, headings,
listas, tabela simples, datas, links e seções vazias. Casos adversariais incluem extensão falsa,
assinatura inválida, PDF criptografado/somente-imagem/excesso de páginas, ZIP bomb, relação DOCX
externa, HTML com script/handler, binário, base64 inválido e payload acima do limite.

Cada teste deve conferir hash, tipo detectado, provenance/página, warnings, review inicial
`sourced`, ordem dos blocos e ausência de execução de rede/conteúdo ativo. Nenhuma fixture pode
conter nome, contato, currículo ou caminho pessoal real.
