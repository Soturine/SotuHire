# Setup local

## Requisitos

- Python 3.11 ou superior;
- Git;
- chave de API do provedor de IA escolhido;
- ambiente virtual Python.

## Clonar o repositório

```bash
git clone https://github.com/Soturine/SotuHire.git
cd SotuHire
```

## Criar ambiente virtual

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

## Instalar dependências

```bash
pip install -r docs/requirements/requirements.txt
```

Dependências sugeridas para o MVP:

```text
streamlit
google-genai
pymupdf
pydantic
python-dotenv
pytest
ruff
```

## Configurar ambiente

Crie um arquivo `.env` baseado em `.env.example`:

```text
GEMINI_API_KEY=your_api_key_here
```

Não commite o `.env`.

## Rodar o app

```bash
streamlit run app.py
```

## Rodar testes

```bash
pytest
```

## Rodar lint

```bash
ruff check .
```

## Rodar formatação

```bash
ruff format .
```

## Problemas comuns

### PDF sem texto

O currículo pode estar como imagem. Nesse caso, PyMuPDF pode não extrair texto útil.

### Chave de API ausente

Verifique se `.env` existe e se a variável está correta.

### JSON inválido da IA

Use schema Pydantic e fallback de erro amigável.
