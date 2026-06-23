# Scripts locais do SotuHire

Este guia descreve os scripts locais da experiência web-first. O fluxo principal da v1.5.1 é o
frontend moderno em `apps/web` consumindo a FastAPI local em `apps/api`.

## Comando principal

Na raiz do repositório:

```powershell
.\start-sotuhire.ps1
```

O launcher:

- verifica se Python existe;
- verifica se Node/npm existem;
- confirma que o comando está na raiz do repositório;
- configura CORS local;
- inicia a API com `python scripts/run_api.py`;
- inicia o frontend com `npm run dev`;
- roda `npm install` apenas quando necessário;
- espera `/api/v1/health`;
- espera o Vite subir;
- abre `http://localhost:5173`;
- encerra processos filhos com `Ctrl+C`.

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

- `-NoBrowser`: não abre o navegador automaticamente.
- `-SkipInstall`: não roda `npm install`.
- `-ApiOnly`: sobe apenas a API.
- `-WebOnly`: sobe apenas o frontend.
- `-Production`: usa build/preview do frontend.
- `-WithCompanion`: inicia a Local Companion API existente para a extensão assistiva.

`-WithCompanion` não abre navegador autenticado, não faz login, não altera Chromium/CDP e não muda o
fluxo de coleta autenticada existente.

## PowerShell execution policy

Se o PowerShell bloquear scripts locais, abra um terminal no repositório e use uma política apenas
para a sessão atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-sotuhire.ps1
```

Evite alterar a política global se não for necessário.

## CORS local

O launcher configura por padrão:

```txt
SOTUHIRE_API_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173
```

Se a variável já existir no ambiente, o script respeita o valor informado.

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

Local Companion API, quando necessária para a extensão:

```powershell
python -m modules.local_api.server
```

## Como parar

Use `Ctrl+C` no terminal do launcher. O script tenta encerrar API, frontend e companion iniciados por
ele. Logs locais ficam em `.sotuhire/logs/`.

## Streamlit

O Streamlit continua disponível como modo legado/dev/debug local:

```powershell
streamlit run app.py
```

Ele não é iniciado pelo launcher web-first.

## Erros comuns

- **Python não encontrado**: instale Python 3.11+ e confira se `python` está no `PATH`.
- **Node/npm não encontrados**: instale Node.js e rode novamente.
- **Porta 8787 ocupada**: encerre o processo que está usando a porta da API.
- **Porta 5173 ocupada**: encerre outro Vite aberto ou rode o frontend manualmente em outra porta.
- **Porta 8765 ocupada**: outra Local Companion API já está aberta; feche ou rode sem
  `-WithCompanion`.
- **Frontend não sobe**: rode `cd apps/web; npm install; npm run build` para ver o erro completo.
- **CORS no modo API Real**: confirme que a API foi iniciada pelo launcher ou defina
  `SOTUHIRE_API_ALLOWED_ORIGINS` com a origem do frontend.
- **Companion offline**: rode `.\start-sotuhire.ps1 -WithCompanion` ou
  `python -m modules.local_api.server`.
- **API health não responde**: verifique se `python scripts/run_api.py` sobe sem erro e se a porta
  8787 está livre.
