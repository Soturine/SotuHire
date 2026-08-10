# Segurança de dependências

## Política v1.11.0

- PR Dependabot é referência, nunca fonte de código.
- Actions são pins por SHA completo com comentário da versão.
- npm usa lockfile regenerado pelo npm; não há `audit fix --force` nem override de nanoid.
- Python mantém ranges deliberados e tooling pinado quando a reprodutibilidade importa.

## Resultado local

`npm audit` encontrou zero vulnerabilidades. Vite/PostCSS passou a resolver `nanoid 3.3.18`, acima
do fix 3.3.17. `pip-audit -r docs/requirements/requirements.txt` encontrou zero vulnerabilidades
nas dependências resolvidas do projeto em 2026-08-10.

Um audit inicial sem `-r` encontrou vulnerabilidades no ambiente Python global compartilhado,
inclusive em pacotes não declarados pelo SotuHire (`llama-stack`, GitPython e outros). Esse número
não representa o produto. `pip list --outdated` também é inventário do ambiente, não autorização
para bulk update; majors de pandas, Playwright, Markdown e outros seguem fora deste release.

PyMuPDF foi removido por decisão de licenciamento; consulte
[Licenciamento do pipeline PDF](pdf-renderer-licensing.md).

