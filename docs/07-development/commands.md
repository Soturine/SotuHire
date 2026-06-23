# Comandos úteis

## Ambiente

Criar ambiente:

```bash
python -m venv .venv
```

Ativar no Windows PowerShell:

```powershell
.venv\Scripts\activate
```

Ativar no Git Bash:

```bash
source .venv/Scripts/activate
```

Ativar no Linux/macOS:

```bash
source .venv/bin/activate
```

## Dependências

Instalar:

```bash
pip install -r docs/requirements/requirements.txt
```

Atualizar pip:

```bash
python -m pip install --upgrade pip
```

## App

Fluxo local principal:

```powershell
.\start-sotuhire.ps1
```

Sem abrir navegador:

```powershell
.\start-sotuhire.ps1 -NoBrowser
```

Rodar Streamlit legado/dev:

```powershell
streamlit run app.py
```

Rodar FastAPI local:

```powershell
python scripts/run_api.py
```

Rodar frontend moderno manualmente:

```powershell
cd apps/web
npm install
npm run dev
```

OpenAPI:

```text
http://127.0.0.1:8787/openapi.json
http://127.0.0.1:8787/docs
```

## Testes

Rodar todos:

```bash
pytest
```

Com detalhes:

```bash
pytest -v
```

Com coverage, se instalado:

```bash
pytest --cov=modules --cov-report=term-missing
```

## Ruff

Lint:

```bash
ruff check .
```

Corrigir automaticamente o que for seguro:

```bash
ruff check . --fix
```

Formatar:

```bash
ruff format .
```

Checar formatação sem alterar:

```bash
ruff format . --check
```

Fluxo recomendado antes de commit:

```bash
ruff check .
ruff format . --check
pytest
```

## MkDocs

Rodar docs localmente:

```bash
mkdocs serve
```

Build:

```bash
mkdocs build
```

Deploy no GitHub Pages, quando fizer sentido:

```bash
mkdocs gh-deploy
```

## Playwright futuro

Instalar plugin:

```bash
pip install pytest-playwright
playwright install
```

Usar apenas quando houver testes E2E ou páginas públicas dinâmicas.

## Git

Ver status:

```bash
git status
```

Adicionar arquivos:

```bash
git add .
```

Commit para docs:

```bash
git commit -m "docs: expand scraping and quality documentation"
```

Commit para MVP:

```bash
git commit -m "feat: add initial resume job match MVP"
```

Enviar:

```bash
git push
```

## Aplicar patch

```bash
git apply SotuHire-scraping-ruff-update.patch
```

Depois:

```bash
git add .
git commit -m "docs: expand scraping strategy and Ruff setup"
git push
```
