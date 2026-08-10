# Licenciamento do pipeline PDF

## Decisão da v1.11.0

O runtime Apache-2.0 não distribui mais PyMuPDF. A dependência foi substituída por:

- `pypdf` para leitura e extração de texto;
- `ReportLab` para geração determinística de PDF A4/Letter.

Ambos declaram licença BSD nas páginas verificadas do PyPI. PyMuPDF declara licenciamento duplo
AGPL-3.0/comercial. Esta diferença impede afirmar, sem análise jurídica e sem cumprir AGPL ou obter
licença comercial, que a distribuição Apache-2.0 anterior era compatível.

Fontes oficiais consultadas em 2026-08-10:

- <https://pypi.org/project/pymupdf/>;
- <https://pypi.org/project/pypdf/>;
- <https://github.com/py-pdf/pypdf/blob/main/LICENSE>;
- <https://pypi.org/project/reportlab/>.

Esta é uma decisão técnica de redução de risco, não aconselhamento jurídico.

## Limites e regressão

- PDFs protegidos por senha continuam rejeitados.
- O limite de 200 páginas e o estado `needs_review` para PDF sem texto permanecem.
- Não há OCR silencioso.
- Exports continuam selecionáveis, sem rede, com dimensões A4/Letter e conteúdo canônico.
- Os testes verificam extração, criptografia, PDF somente-imagem, tamanho de página, metadados e
  fidelidade entre JSON Resume, PDF e DOCX.
