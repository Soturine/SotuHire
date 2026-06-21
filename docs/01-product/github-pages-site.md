# GitHub Pages vs App Local

## Resumo

O GitHub Pages do SotuHire é um site estático para documentação, visão de produto, roadmap e demos
visuais. Ele não executa Python, Streamlit, Gemini, Local Companion API, extensão ou qualquer
backend.

## O que roda no GitHub Pages

- documentação MkDocs;
- páginas de produto;
- roadmap;
- prompt playbooks;
- explicações do Match Engine 2.0;
- demos estáticas fictícias;
- links para instalação, releases e repositório.

## O que não roda no GitHub Pages

- app Streamlit;
- análise de currículo e vaga em tempo real;
- Local Companion API;
- integração com extensão;
- Gemini;
- escrita em memória local;
- tracker local;
- leitura de arquivos do computador.

## Como usar o app real

Rode localmente:

```bash
pip install -r docs/requirements/requirements.txt
streamlit run app.py
```

O modo local-first é parte do design do produto. Currículos, histórico e memória ficam no
computador da pessoa usuária por padrão.

## Como usar o site público

Use o site para:

- entender o produto;
- navegar pela documentação;
- mostrar o projeto como portfolio;
- consultar regras de negócio;
- revisar prompts;
- acessar demos fictícias e releases.

## Regra de comunicação

Nunca apresentar o GitHub Pages como app online completo. A mensagem correta é:

```txt
GitHub Pages é a vitrine/documentação estática. O app completo roda localmente.
```
