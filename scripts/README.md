# Scripts locais do SotuHire

## Launcher web-first

Na raiz do repositório:

```powershell
.\start-sotuhire.ps1
```

Esse comando inicia a API FastAPI em `http://127.0.0.1:8787`, inicia o frontend
moderno em `http://localhost:5173`, aguarda `/api/v1/health`, aguarda o Vite e
abre o navegador.

URLs úteis:

```txt
API: http://127.0.0.1:8787
API docs: http://127.0.0.1:8787/docs
Frontend: http://localhost:5173
Local Companion opcional: http://127.0.0.1:8765
```

Flags:

```powershell
.\start-sotuhire.ps1 -NoBrowser
.\start-sotuhire.ps1 -SkipInstall
.\start-sotuhire.ps1 -ApiOnly
.\start-sotuhire.ps1 -WebOnly
.\start-sotuhire.ps1 -Production
.\start-sotuhire.ps1 -WithCompanion
```

`-WithCompanion` inicia a Local Companion API já existente para a extensão
assistiva. Isso não abre navegador autenticado, não faz login e não altera a
lógica de coleta.

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

Local Companion API, quando necessário para a extensão:

```powershell
python -m modules.local_api.server
```

## Streamlit

O Streamlit continua disponível como modo legado/dev/debug local. Ele não é
iniciado pelo launcher web-first.

## Solução de problemas

- **Python não encontrado**: instale Python 3.11+ e confira se `python` está no
  `PATH`.
- **Node/npm não encontrados**: instale Node.js e rode novamente.
- **Porta 8787 ocupada**: encerre o processo que está usando a porta da API.
- **Porta 5173 ocupada**: encerre outro Vite aberto ou rode o frontend manualmente
  em outra porta.
- **Frontend não sobe**: rode `cd apps/web; npm install; npm run build` para ver o
  erro completo.
- **CORS no modo API Real**: confirme que a API foi iniciada pelo launcher ou
  defina `SOTUHIRE_API_ALLOWED_ORIGINS` com a origem do frontend.
- **Companion offline**: rode `.\start-sotuhire.ps1 -WithCompanion` ou
  `python -m modules.local_api.server`.
- **Ctrl+C**: o launcher encerra os processos filhos e grava logs em
  `.sotuhire/logs/`.
