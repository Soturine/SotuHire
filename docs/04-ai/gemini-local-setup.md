# Setup Local do Gemini

## Análise local

O SotuHire funciona sem chave e sem SDK externo. A análise local é determinística, explicável e permanece como opção padrão:

```env
DEFAULT_AI_PROVIDER=local
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

## Ativar Gemini pela interface

1. Abra o SotuHire.
2. Expanda `Configurar IA` na sidebar.
3. Clique em `Abrir Google AI Studio`.
4. Crie e copie uma chave.
5. Cole a chave no campo seguro.
6. Clique em `Testar Gemini`.
7. Clique em `Salvar configuração local`.
8. O app selecionará Gemini no rerun seguinte.

O Google AI Studio é aberto em `https://aistudio.google.com/app/apikey`.

## Instalar o SDK

```bash
pip install -r requirements-ai.txt
```

O SDK usado é `google-genai`.

## Onde a configuração fica

O wizard salva:

```text
.streamlit/secrets.toml
```

Esse arquivo e `.env` estão no `.gitignore`. Nunca versione chaves reais.

## Variáveis e aliases

Padrão atual:

```env
DEFAULT_AI_PROVIDER=gemini
GEMINI_API_KEY=sua_chave
GEMINI_MODEL=gemini-2.5-flash
```

Aliases compatíveis:

- `LLM_PROVIDER`;
- `LLM_MODEL`;
- `GOOGLE_API_KEY`.

As variáveis canônicas têm precedência.

## Selecionado versus usado

A análise selecionada é a intenção da pessoa usuária. A análise realmente usada é a que produziu o resultado.

Se Gemini falhar por chave ausente, SDK ausente, autenticação ou indisponibilidade, o SotuHire usa análise local e mostra o motivo. Detalhes internos ficam recolhidos em `Detalhes técnicos da análise`.

## Segurança

- o teste do Gemini só ocorre após clique explícito;
- currículo e vaga só são enviados ao Gemini quando ele está selecionado;
- o histórico local não salva os textos brutos;
- `.env` e `.streamlit/secrets.toml` não devem ser commitados.

## Teste simples versus estruturado

`Testar Gemini simples` envia somente:

```text
Responda apenas: ok
```

Não há schema estruturado. Uma falha aqui aponta para chave, modelo, SDK, quota, região ou projeto.

`Testar Gemini estruturado` usa uma entrada fictícia pequena e o schema real do SotuHire. Se o teste simples passar e este falhar, revise schema e payload.

## Diagnóstico de 400 INVALID_ARGUMENT

O wizard mostra:

- código recebido;
- motivo resumido;
- modelo usado;
- versão do SDK;
- variável encontrada;
- tipo de chamada;
- erro bruto resumido e sanitizado.

`INVALID_ARGUMENT` no teste simples sugere testar outro modelo. No teste estruturado, sugere comparar com o teste simples e revisar o schema.

Modelos disponíveis no seletor:

```text
gemini-2.5-flash
gemini-2.5-pro
gemini-1.5-flash
```

O padrão continua vindo de `GEMINI_MODEL`.
