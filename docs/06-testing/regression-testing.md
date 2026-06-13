# Testes de Regressão

## Escopo da v0.5.0

As regressões automatizadas cobrem:

- setup e salvamento local do Gemini;
- mensagens amigáveis quando Gemini está indisponível;
- compatibilidade com aliases antigos;
- modo rápido e análise de exemplo;
- vaga vazia e vaga de exemplo;
- remoção de prefixos e duplicatas em skills;
- separação de soft skills;
- carregamento de todas as fixtures;
- comparação com expected outputs;
- histórico vazio e persistido;
- métricas e filtros do dashboard.

## Comandos

```bash
pyright
ruff check .
ruff format . --check
python -m pytest -q
mkdocs build --strict
```

## Teste Streamlit

`tests/test_auto_flow.py` usa `streamlit.testing.v1.AppTest` para clicar em `Rodar análise de exemplo` e confirmar que currículo, vaga, análise e Resume Tailor são preenchidos sem preferências manuais.

O smoke test final também inicia:

```bash
streamlit run app.py
```

e verifica o endpoint de saúde.

## Novas regressões

Ao corrigir um caso real, primeiro crie uma fixture fictícia mínima ou um teste focado. Não use currículo real como fixture versionada.
