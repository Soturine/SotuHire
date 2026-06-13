# Testes de Screenshots

## Objetivo

Os screenshots da v0.6.0 demonstram o fluxo real do Streamlit sem usar dados pessoais. Eles são gerados com as fixtures fictícias do repositório e referenciados pelo README.

## Arquivos esperados

```text
docs/assets/screenshots/sotuhire-v0.6-home.png
docs/assets/screenshots/sotuhire-v0.6-resume.png
docs/assets/screenshots/sotuhire-v0.6-job.png
docs/assets/screenshots/sotuhire-v0.6-result.png
docs/assets/screenshots/sotuhire-v0.6-dashboard.png
docs/assets/screenshots/sotuhire-v0.6-ai-setup.png
```

## Captura reproduzível

Instale as dependências e o navegador:

```bash
pip install -r requirements-dev.txt
playwright install chromium
```

Com o app em execução, capture:

```bash
streamlit run app.py
python scripts/capture_screenshots.py --url http://localhost:8501
```

O script navega pelas experiências rápida e avançada, usa a demo local e salva imagens PNG.

## Regressão

`tests/test_readme_screenshots.py` verifica que:

- o README referencia os seis arquivos;
- todos existem;
- cada imagem tem tamanho útil;
- nenhum arquivo excede o limite definido pelo teste.

Antes de publicar uma versão, recapture as imagens depois de atualizar o badge de versão e confirme visualmente que não há segredos nem dados reais.
