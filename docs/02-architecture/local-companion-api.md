# Local Companion API

A Local Companion API conecta a extensão assistiva ao SotuHire sem publicar um serviço na rede.
Ela usa a biblioteca padrão do Python, escuta somente em `127.0.0.1:8765` e persiste dados nos
stores locais ignorados pelo Git.

## Endpoints

| Endpoint | Uso |
| --- | --- |
| `GET /health` | testa a conexão local sem expor segredos |
| `POST /capture/job` | normaliza e salva a vaga atual |
| `POST /capture/analyze` | analisa a captura com contexto ativo |
| `POST /capture/tracker` | analisa e envia a captura ao tracker |
| `POST /capture/applications` | importa um lote de candidaturas já realizadas |
| `POST /capture/github-profile` | analisa um perfil GitHub público |
| `POST /capture/github-repo` | analisa um repositório público |
| `POST /capture/portfolio` | analisa um portfólio público |
| `POST /capture/project` | analisa uma página pública de projeto |
| `POST /capture/repo-analysis` | gera e salva relatório completo |
| `POST /capture/commit-analysis` | gera relatório com sinais de commits |

## Contexto ativo

A aba **Extensão** sincroniza currículo, preferências e nome do provider em
`data/companion/active-context.json`. Quando a extensão solicita IA, a API usa o provider e a chave
configurados no processo local. A chave nunca entra no payload ou na resposta.

## Identidade multiportal

Capturas, oportunidades e cartões usam uma identidade estável:

1. URL sem query string e fragmento;
2. empresa normalizada + título com similaridade forte.

Assim, uma vaga descoberta no LinkedIn e concluída na Gupy, por exemplo, mantém um único cartão,
uma única memória e uma lista com todas as URLs/domínios de origem.

## Segurança

- bind obrigatório em loopback;
- token `SOTUHIRE_COMPANION_TOKEN` opcional;
- contratos Pydantic com limites;
- sanitização de texto visível;
- nenhum log de conteúdo completo ou chave;
- nenhum login, senha, cookie ou CAPTCHA tratado pela API.

Para projetos, a API também nunca recebe a chave Gemini standalone da extensão. Quando solicitado,
o aprimoramento Gemini conectado usa somente a configuração local do SotuHire e preserva os scores
determinísticos.

## Iniciar

Use o botão **Iniciar Local API** na aba avançada **Extensão**. Para desenvolvimento:

```python
from modules.local_api import start_server

start_server()
```
