# Scripts locais do SotuHire

Este guia descreve os scripts locais da experiencia web-first. O fluxo principal da v1.6.0 e o
frontend moderno em `apps/web` consumindo a FastAPI local em `apps/api`.

## Comando principal

Na raiz do repositorio:

```powershell
.\start-sotuhire.ps1
```

O launcher:

- verifica se Python existe;
- verifica se Node/npm existem;
- confirma que o comando esta na raiz do repositorio;
- configura CORS local;
- detecta portas ocupadas e mostra processo/PID;
- inicia a API com `python scripts/run_api.py`;
- inicia o frontend com `npm run dev`;
- roda `npm install` apenas quando necessario;
- espera `/api/v1/health`;
- espera o Vite subir;
- abre `http://localhost:5173`;
- encerra processos filhos com `Ctrl+C`.

Mensagens esperadas:

```txt
API iniciando...
Frontend iniciando...
Companion iniciando...
API online
Frontend online
Companion online
Abra: http://localhost:5173
Docs API: http://127.0.0.1:8787/docs
Pressione Ctrl+C para encerrar
```

## URLs e portas

```txt
API: http://127.0.0.1:8787
API docs: http://127.0.0.1:8787/docs
Frontend: http://localhost:5173
Preview production: http://localhost:4173
Local Companion opcional: http://127.0.0.1:8765
Chromium/CDP manual opcional: http://127.0.0.1:9222
```

## Flags

```powershell
.\start-sotuhire.ps1 -NoBrowser
.\start-sotuhire.ps1 -SkipInstall
.\start-sotuhire.ps1 -ApiOnly
.\start-sotuhire.ps1 -WebOnly
.\start-sotuhire.ps1 -Production
.\start-sotuhire.ps1 -WithCompanion
```

- `-NoBrowser`: nao abre o navegador automaticamente.
- `-SkipInstall`: nao roda `npm install`.
- `-ApiOnly`: sobe apenas a API.
- `-WebOnly`: sobe apenas o frontend.
- `-Production`: usa build/preview do frontend.
- `-WithCompanion`: inicia a Local Companion API existente para a extensao assistiva.

`-WithCompanion` nao abre navegador autenticado, nao faz login, nao altera Chromium/CDP e nao muda o
fluxo de coleta autenticada existente.

## PowerShell execution policy

Se o PowerShell bloquear scripts locais, abra um terminal no repositorio e use uma politica apenas
para a sessao atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-sotuhire.ps1
```

Evite alterar a politica global se nao for necessario.

## CORS local

O launcher configura por padrao:

```txt
SOTUHIRE_API_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173
```

Se a variavel ja existir no ambiente, o script respeita o valor informado.

## Modo manual

API:

```powershell
python scripts/run_api.py
```

Frontend:

```powershell
cd apps/web
npm install
npm run dev
```

Local Companion API, quando necessaria para a extensao:

```powershell
python -m modules.local_api.server
```

## Como parar

Use `Ctrl+C` no terminal do launcher. O script tenta encerrar API, frontend e companion iniciados por
ele. Logs locais ficam em `.sotuhire/logs/`.

## Streamlit

O Streamlit continua disponivel como modo legado/dev/debug local:

```powershell
streamlit run app.py
```

Ele nao e iniciado pelo launcher web-first.

## Erros comuns

- **Python nao encontrado**: instale Python 3.11+ e confira se `python` esta no `PATH`.
- **Node/npm nao encontrados**: instale Node.js e rode novamente.
- **Porta 8787 ocupada**: o launcher mostra processo/PID. Encerre esse processo ou rode depois.
- **Porta 5173 ocupada**: encerre outro Vite aberto ou rode o frontend manualmente em outra porta.
- **Porta 8765 ocupada**: outra Local Companion API ja esta aberta; feche ou rode sem
  `-WithCompanion`.
- **Frontend nao sobe**: rode `cd apps/web; npm install; npm run build` para ver o erro completo.
- **CORS no modo API Real**: confirme que a API foi iniciada pelo launcher ou defina
  `SOTUHIRE_API_ALLOWED_ORIGINS` com a origem do frontend.
- **Companion offline**: rode `.\start-sotuhire.ps1 -WithCompanion` ou
  `python -m modules.local_api.server`.
- **API health nao responde**: verifique se `python scripts/run_api.py` sobe sem erro e se a porta
  8787 esta livre.
