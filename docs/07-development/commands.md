# Comandos úteis

## Ambiente

```bash
python -m venv .venv
```

Ativar no Windows:

```bash
.venv\Scripts\activate
```

Ativar no Linux/macOS:

```bash
source .venv/bin/activate
```

## Dependências

```bash
pip install -r requirements.txt
```

Gerar requirements a partir do ambiente atual:

```bash
pip freeze > requirements.txt
```

## App

```bash
streamlit run app.py
```

## Testes

```bash
pytest
```

Com detalhes:

```bash
pytest -v
```

## Lint

```bash
ruff check .
```

## Format

```bash
ruff format .
```

## Git

```bash
git status
git add .
git commit -m "docs: rebuild project documentation"
git push
```
