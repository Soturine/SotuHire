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
pip install -r docs/requirements/requirements-dev.txt
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

## Screenshots da v0.7.0

A v0.7.0 amplia a captura para oito superfícies: modo rápido, modo avançado, coleta, oportunidades coletadas, Search Intelligence, Hidden Jobs Radar, resultado e dashboard.

Antes de abrir o navegador, o script grava uma oportunidade fictícia no store local ignorado pelo Git. Assim, a tela de oportunidades coletadas é reproduzível sem depender de rede nem de dados pessoais.

## Screenshots da v0.8.0

A v0.8.0 adiciona capturas com dados fictícios para visão geral da memória, perfil profissional,
evidências da análise e busca na memória. O README referencia apenas a visão geral atual para
continuar intuitivo; as demais imagens apoiam a documentação e a validação visual.

O script atual gera somente as quatro superfícies da v0.8.0. As capturas anteriores permanecem no
repositório como registro visual histórico e não são sobrescritas.

## Screenshots da v0.9.0

A v0.9.0 registra a aba Extensão, popup, vaga capturada, feedback de evidência e perfil
profissional. Todas as capturas usam dados fictícios. O README continua referenciando somente uma
imagem atual para permanecer intuitivo; as demais ficam na documentação da versão.

O complemento GitHub/Portfólio adiciona cinco capturas: análise no popup, relatório de repositório,
GitHub Profile Score, análise de commits e evidência de projeto.

## Screenshots da v1.1.0

A v1.1.0 separa duas famílias de captura:

- Streamlit local: screenshots reais do app atual/dev usados no README raiz.
- MkDocs/GitHub Pages: screenshots do site público estático usados em `visual-preview.md`.

Para recapturar o app Streamlit:

```bash
streamlit run app.py
python scripts/capture_streamlit_v1_1_screenshots.py --url http://localhost:8501
```

Para recapturar o site MkDocs:

```bash
mkdocs serve
python scripts/capture_docs_screenshots.py --base-url http://127.0.0.1:8000/SotuHire/ --gif
```

Todas as imagens devem usar dados fictícios e não podem mostrar API keys, tokens ou currículos reais.
